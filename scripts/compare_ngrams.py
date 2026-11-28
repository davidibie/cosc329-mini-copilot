"""Evaluate all 20 n-grams on the five pinned development folds."""

import argparse
import hashlib
import math
import json
import platform
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation import evaluate, word_cases
from ngram_models import END_WORD, CharacterNGramModel, WordNGramModel
from scripts.prepare_data import read_sources
from text_processing import prediction_context


def load_cases(manifest_path, projects, raw, max_per_file=None):
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    files = [item for item in manifest['files'] if item['project'] in projects]
    sources = read_sources(manifest_path, projects, raw)
    for item, source in zip(files, sources, strict=True):
        file_cases = list(word_cases(source, f"{item['project']}/{item['path']}"))
        if max_per_file and len(file_cases) > max_per_file:
            file_cases = sorted(file_cases, key=lambda case: hashlib.sha256(
                f"{manifest['seed']}:{case.id}".encode()).digest())[:max_per_file]
            file_cases.sort(key=lambda case: case.offset)
        yield from file_cases


def character_ranker(model):
    """Share character transitions across candidates with the same prefix."""
    size = model.n - 1
    # Keep prefixes of known histories as well as the histories themselves.
    # A later character can extend one of these into a known history.
    states = {''.join(key[:length]) for key in model.counts for length in range(len(key) + 1)}

    def state_for(history):
        while history not in states and history:
            history = history[1:]
        return history

    @lru_cache(maxsize=65536)
    def transition(state, symbol):
        history = (state + symbol)[-size:] if size else ''
        return state_for(history), math.log(model.probability(symbol, state))

    @lru_cache(maxsize=32)
    def candidate_trie(partial):
        nodes = {}
        for word in sorted(model.vocabulary):
            if not word.startswith(partial) or len(word) <= len(partial):
                continue
            node = nodes
            for symbol in word[len(partial):]:
                node = node.setdefault(symbol, {})
            node[END_WORD] = word
        return nodes

    @lru_cache(maxsize=32768)
    def rank(state, partial):
        scores = {}
        stack = [(candidate_trie(partial), state, 0.0)]
        while stack:
            node, state, score = stack.pop()
            for symbol, child in node.items():
                next_state, log_probability = transition(state, symbol)
                subtotal = score + log_probability
                if symbol == END_WORD:
                    scores[child] = subtotal / (len(child) - len(partial) + 1)
                else:
                    stack.append((child, next_state, subtotal))
        return tuple(sorted(scores, key=lambda word: (-scores[word], word))[:5])

    return lambda history, partial: rank(state_for(history), partial)


def cached_ranker(model, family, contexts):
    """Reuse rankings for prefixes that produce identical n-gram scores."""
    size = model.n - 1

    @lru_cache(maxsize=32768)
    def rank_word(history, partial):
        candidates = [word for word in model.vocabulary if word.startswith(partial)
                      and len(word) > len(partial)]
        counts = model.counts.get(history, {})
        # Compute the same smoothed probabilities as the public predictor.
        denominator = model.totals.get(history, 0) + model.alpha * (len(model.symbols) + 1)
        return tuple(sorted(candidates, key=lambda word: (
            -(counts.get(word, 0) + model.alpha) / denominator, word))[:5])

    rank_character = character_ranker(model) if family == 'character' else None

    def suggest(case):
        context = contexts[case.id]
        if context is None:
            return ()
        names, partial = context
        if rank_character is not None:
            history = case.source[max(0, case.offset - size):case.offset]
            return rank_character(history, partial)
        history = tuple(names[-size:]) if size else ()
        while history and history not in model.counts:
            history = history[1:]
        return rank_word(history, partial)

    return suggest


def run_fold(args, fold):
    train = list(read_sources(args.manifest, fold['train_projects'], args.raw))
    cases = list(load_cases(args.manifest, fold['validation_projects'], args.raw, args.max_per_file))
    contexts = {}
    for case in cases:
        context = prediction_context(case.prefix)
        contexts[case.id] = None if context is None else (context[0][-9:], context[1])
    rows = []
    for family, model_class in [('word', WordNGramModel), ('character', CharacterNGramModel)]:
        for n in range(1, 11):
            model = model_class(n, args.alpha)
            start = perf_counter()
            model.fit(train)
            fit_seconds = perf_counter() - start
            metrics = evaluate(model, cases, suggest_case=cached_ranker(model, family, contexts))
            rows.append({'fold': fold['fold'], 'family': family, 'n': n,
                         'fit_seconds': fit_seconds, 'vocabulary_size': len(model.vocabulary), **metrics})
            print(f"Fold {fold['fold']} {family} {n}: {metrics['top1_accuracy']:.3%}", flush=True)
    digest = hashlib.sha256('\n'.join(case.id for case in cases).encode()).hexdigest()
    return {'split': fold, 'case_ids_sha256': digest, 'models': rows}


def summarize(folds):
    rows = [row for fold in folds for row in fold['models']]
    summary = []
    for family in ('word', 'character'):
        for n in range(1, 11):
            models = [row for row in rows if row['family'] == family and row['n'] == n]
            stats = {}
            for name in ('top1_accuracy', 'top5_accuracy', 'mean_edit_distance'):
                values = [row[name] for row in models]
                stats[name] = {'mean': statistics.mean(values), 'sample_sd': statistics.stdev(values)}
            summary.append({'family': family, 'n': n, **stats})
    return sorted(summary, key=lambda row: (-row['top1_accuracy']['mean'],
                                            row['mean_edit_distance']['mean'], row['n'], row['family']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'data/manifest.json')
    parser.add_argument('--raw', type=Path, default=ROOT / 'data/raw')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-per-file', type=int, help='Optional deterministic case cap for quick runs')
    parser.add_argument('--alpha', type=float, default=1.0)
    parser.add_argument('--workers', type=int, default=1)
    args = parser.parse_args()
    if args.max_per_file is not None and args.max_per_file < 1:
        parser.error('--max-per-file must be positive')
    raw_manifest = args.manifest.read_bytes()
    folds = json.loads(raw_manifest)['folds']
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        results = [executor.submit(run_fold, args, fold) for fold in folds]
        folds = [result.result() for result in results]
    summary = summarize(folds)
    output = {'manifest_sha256': hashlib.sha256(raw_manifest).hexdigest(),
              'python_version': platform.python_version(), 'platform': platform.platform(),
              'workers': args.workers, 'alpha': args.alpha, 'max_per_file': args.max_per_file,
              'folds': folds, 'summary': summary, 'selected': summary[0]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
