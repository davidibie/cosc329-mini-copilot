import hashlib
import json
import unittest
from pathlib import Path
from scripts.prepare_data import project_splits, read_sources

ROOT = Path(__file__).resolve().parents[1]


class DatasetTests(unittest.TestCase):
    def test_split_is_repeatable_and_disjoint(self):
        names = [f'project-{i}' for i in range(20)]
        split = project_splits(names, 329)
        self.assertEqual(split, project_splits(reversed(names), 329))
        development, test = set(split['development_projects']), set(split['test_projects'])
        self.assertEqual((len(development), len(test)), (14, 6))
        self.assertFalse(development & test)
        validated = []
        for fold in split['folds']:
            train, validation = set(fold['train_projects']), set(fold['validation_projects'])
            self.assertTrue(validation)
            self.assertFalse(train & validation)
            self.assertEqual(train | validation, development)
            self.assertFalse((train | validation) & test)
            validated.extend(validation)
        self.assertCountEqual(validated, development)

    def test_saved_manifest_has_no_duplicates(self):
        manifest = json.loads((ROOT / 'data/manifest.json').read_text())
        files = manifest['files']
        for field in ('sha256', 'token_sha256'):
            self.assertEqual(len({item[field] for item in files}), len(files))
        self.assertEqual(len({item['project'] for item in files}), 20)
        self.assertTrue(all(item['name_tokens'] >= 10 for item in files))

    def test_available_source_bytes_match_manifest(self):
        manifest = json.loads((ROOT / 'data/manifest.json').read_text())
        if not (ROOT / 'data/raw').exists():
            self.skipTest('Run scripts/prepare_data.py to verify source bytes locally')
        sources = list(read_sources(ROOT / 'data/manifest.json', manifest['development_projects']))
        self.assertEqual(len(sources), sum(f['project'] in manifest['development_projects'] for f in manifest['files']))
        with self.assertRaises(ValueError):
            list(read_sources(ROOT / 'data/manifest.json', ['unknown-project']))


if __name__ == '__main__':
    unittest.main()
