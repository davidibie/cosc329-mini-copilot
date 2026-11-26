import json
import math
import tempfile
import unittest
from pathlib import Path

from ngram_models import CharacterNGramModel, WordNGramModel
from text_processing import prediction_context, word_tokens

FAMILIES = (WordNGramModel, CharacterNGramModel)


class TokenTests(unittest.TestCase):
    def test_excludes_literals_and_fstring_interpolations(self):
        source = 'result = f"{hidden + another}"\n# ignored\nprint("string", 123)\n'
        self.assertEqual([item.string for item in word_tokens(source)], ['result', 'print'])

    def test_incomplete_prefixes_and_unicode(self):
        self.assertEqual(prediction_context('call(value, pri'), (['call', 'value'], 'pri'))
        self.assertEqual(prediction_context('count = café'), (['count'], 'café'))
        for prefix in ['# pri', 'value = "pri', 'value = """pri', 'value = f"{pri', 'value = 12pri', 'value = 123']:
            with self.subTest(prefix=prefix):
                self.assertIsNone(prediction_context(prefix))


class EditorIntegrationTests(unittest.TestCase):
    def test_fake_predictor_uses_shared_lexical_guard(self):
        from editor import FakePredictor
        predictor = FakePredictor()
        self.assertEqual(predictor.suggest('pri'), ['print'])
        self.assertEqual(predictor.suggest('value = "pri'), [])
        self.assertEqual(predictor.suggest('# pri'), [])
        self.assertEqual(predictor.suggest('f"{pri'), [])
        self.assertEqual(predictor.suggest('call(pri'), ['print'])


class ModelTests(unittest.TestCase):
    def test_all_orders_both_families(self):
        for family in FAMILIES:
            for n in range(1, 11):
                with self.subTest(family=family.__name__, n=n):
                    model = family(n)
                    self.assertEqual(model.suggest(''), [])
                    model.fit(['print(value)\nprint(other)\nproperty = value\n'])
                    self.assertEqual(model.suggest('pri'), ['print'])
                    self.assertEqual(model.suggest('pri', 0), [])
                    self.assertEqual(model.suggest('unseenprefix'), [])
                    self.assertEqual(model.suggest('# pri'), [])
                    self.assertEqual(model.suggest('print'), [])
                    suggestions = model.suggest('', 100)
                    self.assertEqual(set(suggestions), model.vocabulary)
                    self.assertEqual(len(suggestions), len(set(suggestions)))
                    self.assertTrue(all(math.isfinite(model.probability('never-seen', ('missing',))) for _ in range(1)))

    def test_word_counts_smoothing_and_unseen_context(self):
        model = WordNGramModel(2, alpha=1)
        model.fit(['left right\nleft right\nleft other'])
        self.assertEqual(model.suggest('left ', 1), ['right'])
        self.assertAlmostEqual(model.probability('right', ['left']), 3 / 7)
        self.assertAlmostEqual(sum(model.probability(word, ['left']) for word in model.vocabulary) + model.probability('unknown', ['left']), 1)
        self.assertGreater(model.probability('unknown', ['missing']), 0)
        self.assertEqual(model.suggest('missing '), model.suggest(''))

    def test_no_context_crosses_files_and_refit_replaces_state(self):
        for family in FAMILIES:
            model = family(3)
            model.fit(['alpha', 'beta'])
            if family is WordNGramModel:
                self.assertNotIn(('alpha',), model.counts)
            model.fit(['gamma'])
            self.assertEqual(model.vocabulary, {'gamma'})
            model.fit([])
            self.assertEqual(model.suggest(''), [])

    def test_character_score_matches_hand_calculation(self):
        model = CharacterNGramModel(1, alpha=1)
        model.fit(['aa'])
        scores = model._scores('', [], '', ['aa'])
        expected = (2 * math.log(3 / 6) + math.log(2 / 6)) / 3
        self.assertAlmostEqual(scores['aa'], expected)
        self.assertAlmostEqual(sum(model.probability(c) for c in model.symbols) + model.probability('z'), 1)

    def test_save_load_restores_ranking_and_future_fit(self):
        for family in FAMILIES:
            for n in (1, 5, 10):
                with self.subTest(family=family.__name__, n=n), tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / 'model.json'
                    model = family(n)
                    model.fit(['alpha beta\nalpha gamma\nprint(beta)'])
                    model.save(path)
                    restored = family.load(path)
                    for prefix in ('', 'a', 'alpha ', 'print('):
                        self.assertEqual(model.suggest(prefix), restored.suggest(prefix))
                    restored.fit(['other'])
                    self.assertEqual(restored.vocabulary, {'other'})
                    payload = json.loads(path.read_text())
                    payload['version'] = 999
                    path.write_text(json.dumps(payload))
                    with self.assertRaises(ValueError):
                        family.load(path)

    def test_unicode_model_reload(self):
        for family in FAMILIES:
            with self.subTest(family=family.__name__), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'model.json'
                model = family(2)
                model.fit(['élan = π\n'])
                model.save(path)
                self.assertEqual(family.load(path).suggest('é'), ['élan'])

    def test_character_context_uses_physical_lines(self):
        model = CharacterNGramModel(2)
        model.fit(['first = "a\u2028b\fc"\nsecond = 1\n'])
        self.assertEqual(model.counts[('\n',)]['s'], 1)
        self.assertEqual(model.counts.get(('\u2028',), {}).get('s', 0), 0)

    def test_invalid_config_and_ties(self):
        for family in FAMILIES:
            for n in (0, 11, 1.5, True):
                with self.assertRaises(ValueError):
                    family(n)
            for alpha in (0, -1, float('inf'), float('nan')):
                with self.assertRaises(ValueError):
                    family(alpha=alpha)
        model = WordNGramModel(1)
        model.fit(['beta alpha'])
        self.assertEqual(model.suggest(''), ['alpha', 'beta'])


if __name__ == '__main__':
    unittest.main()
