"""Fetch pinned sources and create a deterministic, project-grouped corpus."""

import argparse
import ast
import csv
import hashlib
import io
import json
import random
import os
import tempfile
import subprocess
import tokenize
from collections import Counter
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {'tests', 'test', 'docs', 'examples', 'vendor', 'vendored', '_vendor', '__pycache__'}
IGNORED_TOKENS = {tokenize.ENCODING, tokenize.COMMENT, tokenize.NL,
                  tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER}


def git(directory, *args):
    return subprocess.check_output(['git', '-C', str(directory), *args], text=True).strip()


def fetch_project(row, raw):
    directory = raw / row['project_name']
    commit = row['commit_sha']
    if not directory.exists():
        directory.mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(directory)], check=True)
        subprocess.run(['git', '-C', str(directory), 'remote', 'add', 'origin', row['repository_url']], check=True)
    if git(directory, 'remote', 'get-url', 'origin').removesuffix('.git') != row['repository_url'].removesuffix('.git'):
        raise ValueError(f"Unexpected remote for {directory}")
    if git(directory, 'status', '--porcelain', '--untracked-files=no'):
        raise ValueError(f"Tracked source changes in {directory}; restore them before preparing")
    available = subprocess.run(['git', '-C', str(directory), 'cat-file', '-e', commit], capture_output=True)
    if available.returncode:
        subprocess.run(['git', '-C', str(directory), 'fetch', '--depth=1', 'origin', commit], check=True)
    subprocess.run(['git', '-C', str(directory), 'checkout', '--detach', '-q', commit], check=True)
    if git(directory, 'rev-parse', 'HEAD') != commit:
        raise ValueError(f"Commit mismatch in {directory}")
    return directory


def blob(directory, revision, path):
    return subprocess.check_output(['git', '-C', str(directory), 'cat-file', 'blob', f'{revision}:{path}'])


def decode_source(data):
    with io.TextIOWrapper(io.BytesIO(data), encoding=tokenize.detect_encoding(io.BytesIO(data).readline)[0]) as handle:
        return handle.read()


def inspect_file(path, data):
    """Verify syntax and hash tokens to catch comment/whitespace-only copies."""
    source = decode_source(data)
    ast.parse(source, feature_version=(3, 12))
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    canonical = [(item.type, item.string) for item in tokens if item.type not in IGNORED_TOKENS]
    names = sum(item.type == tokenize.NAME for item in tokens)
    if names < 10:
        raise ValueError('fewer than 10 NAME tokens')
    return {'path': path,
            'sha256': hashlib.sha256(data).hexdigest(),
            'token_sha256': hashlib.sha256(json.dumps(canonical, ensure_ascii=False).encode()).hexdigest(),
            'bytes': len(data), 'characters': len(source), 'name_tokens': names}


def project_splits(names, seed):
    projects = sorted(names)
    random.Random(seed).shuffle(projects)
    development_count = int(len(projects) * 0.7)
    if development_count < 5 or development_count == len(projects):
        raise ValueError('Need at least five development projects and a nonempty holdout')
    development = sorted(projects[:development_count])
    holdout = sorted(projects[development_count:])
    shuffled = development.copy()
    random.Random(seed + 1).shuffle(shuffled)
    validation_groups = [sorted(shuffled[index::5]) for index in range(5)]
    folds = [{'fold': index + 1, 'train_projects': sorted(set(development) - set(validation)),
              'validation_projects': validation} for index, validation in enumerate(validation_groups)]
    return {'seed': seed, 'development_projects': development,
            'test_projects': holdout, 'folds': folds}


def prepare(sources, raw, manifest_path, seed=329, max_files=12, max_bytes=49152, fetch=True):
    rows = list(csv.DictReader(sources.open()))
    names = [row['project_name'] for row in rows]
    if len(names) < 10 or len(set(names)) != len(names):
        raise ValueError('Need at least ten uniquely named independent projects')
    seen_bytes, seen_tokens = set(), set()
    files, rejected, licenses = [], [], []
    for row in sorted(rows, key=lambda item: item['project_name']):
        name = row['project_name']
        directory = fetch_project(row, raw) if fetch else raw / name
        if git(directory, 'status', '--porcelain', '--untracked-files=no'):
            raise ValueError(f'Tracked source changes in {directory}')
        if git(directory, 'rev-parse', 'HEAD') != row['commit_sha']:
            raise ValueError(f'Incorrect source revision for {name}')
        revision = row['commit_sha']
        for license_path in row['notes'].split('license_files=')[1].split('|')[0].split(';'):
            licenses.append({'project': name, 'path': license_path,
                             'sha256': hashlib.sha256(blob(directory, revision, license_path)).hexdigest()})
        included = row['included_paths'].split(';')
        entries = subprocess.check_output(
            ['git', '-C', str(directory), 'ls-tree', '-rz', '-l', revision, '--', *included]
        )
        candidates = {}
        for entry in entries.split(b'\0'):
            if entry:
                metadata, encoded_path = entry.split(b'\t', 1)
                mode, kind, _, size = metadata.split()
                path = encoded_path.decode('utf-8')
                if kind == b'blob' and path.endswith('.py'):
                    candidates[path] = (mode, int(size))
        ordered = sorted(candidates, key=lambda p: hashlib.sha256(f'{seed}:{name}:{p}'.encode()).hexdigest())
        accepted = 0
        for relative in ordered:
            mode, size = candidates[relative]
            reason = None
            if mode == b'120000' or EXCLUDED_PARTS.intersection(PurePosixPath(relative).parts):
                reason = 'excluded directory or symlink'
            elif size > max_bytes:
                reason = 'file size limit'
            elif accepted >= max_files:
                reason = 'project sample limit'
            else:
                data = blob(directory, revision, relative)
                try:
                    record = inspect_file(relative, data)
                except (SyntaxError, UnicodeError, LookupError, ValueError, tokenize.TokenError) as error:
                    reason = f'invalid or ineligible Python 3.12 source: {type(error).__name__}'
                else:
                    header = data[:2048].lower()
                    if b'auto-generated' in header or b'autogenerated' in header or b'do not edit' in header:
                        reason = 'generated header'
                    elif record['sha256'] in seen_bytes or record['token_sha256'] in seen_tokens:
                        reason = 'duplicate content or token stream'
                    else:
                        seen_bytes.add(record['sha256'])
                        seen_tokens.add(record['token_sha256'])
                        record.update(project=name, commit_sha=row['commit_sha'])
                        files.append(record)
                        accepted += 1
            if reason:
                rejected.append({'project': name, 'path': relative, 'reason': reason})
        if not accepted:
            raise ValueError(f'No eligible files for {name}')
    splits = project_splits(names, seed)
    manifest = {'version': 1, 'python_grammar': '3.12', 'sampling': {
        'max_files_per_project': max_files, 'max_bytes_per_file': max_bytes,
        'minimum_name_tokens': 10, 'ordering': 'SHA256(seed:project:relative_path)'},
        **splits, 'licenses': licenses, 'files': sorted(files, key=lambda f: (f['project'], f['path'])),
        'excluded': sorted(rejected, key=lambda f: (f['project'], f['path']))}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=manifest_path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            json.dump(manifest, handle, indent=2, ensure_ascii=False)
            handle.write('\n')
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, manifest_path)
    finally:
        temporary.unlink(missing_ok=True)
    counts = Counter(item['project'] for item in files)
    print(f'{len(counts)} projects; {len(files)} files; {sum(f["characters"] for f in files):,} characters')
    print(f'{len(splits["development_projects"])} development projects; {len(splits["test_projects"])} final test projects')
    return manifest


def read_sources(manifest_path, projects, raw=ROOT / 'data/raw'):
    """Yield only requested projects, verifying bytes against the saved manifest."""
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    known = set(manifest['development_projects'] + manifest['test_projects'])
    projects = set(projects)
    if not projects <= known:
        raise ValueError('Requested project is absent from the manifest')
    for item in manifest['files']:
        if item['project'] in projects:
            directory = raw / item['project']
            path = item['path']
            data = blob(directory, item['commit_sha'], path)
            if hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError(f'Corpus hash mismatch: {directory / path}')
            yield decode_source(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, default=ROOT / 'data/sources.csv')
    parser.add_argument('--raw', type=Path, default=ROOT / 'data/raw')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'data/manifest.json')
    parser.add_argument('--seed', type=int, default=329)
    parser.add_argument('--max-files', type=int, default=12)
    parser.add_argument('--max-bytes', type=int, default=49152)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    if args.max_files < 1 or args.max_bytes < 1:
        parser.error('Sampling limits must be positive')
    prepare(args.sources, args.raw, args.manifest, args.seed, args.max_files, args.max_bytes, not args.offline)


if __name__ == '__main__':
    main()
