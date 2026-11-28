"""Hand-worked metrics and shared target/cursor checks."""

import unittest

from evaluation import edit_distance, evaluate, word_cases
from ngram_models import CharacterNGramModel, WordNGramModel
from scripts.compare_ngrams import cached_ranker
from text_processing import prediction_context


class EvaluationTests(unittest.TestCase):
    def test_cases_hide_target_and_exclude_interpolation(self):
        source = 'π = f"{hidden}"\r\n# ignored\r\nprint(π)\r\n'
        cases = list(word_cases(source, 'project/source.py'))
        self.assertEqual([case.target for case in cases], ['π', 'print', 'π'])
        self.assertEqual(cases[1].prefix, 'π = f"{hidden}"\r\n# ignored\r\n')
        self.assertEqual(cases[2].id, 'project/source.py:3:6')

    def test_hand_worked_distances_and_empty_output(self):
        class Predictor:
            def suggest(self, prefix, limit):
                return {'': ['cat'], 'cat ': ['bat', 'dog'], 'cat dog ': []}[prefix]

        cases = list(word_cases('cat dog π', 'fixture'))
        metrics = evaluate(Predictor(), cases)
        self.assertEqual(edit_distance('kitten', 'sitting'), 3)
        self.assertEqual(metrics['top1_accuracy'], 1 / 3)
        self.assertEqual(metrics['top5_accuracy'], 2 / 3)
        self.assertEqual(metrics['mean_edit_distance'], (0 + 3 + 1) / 3)
        self.assertEqual(metrics['empty_outputs'], 1)
        self.assertEqual(metrics['failures'], {})

    def test_cached_ranker_matches_public_prediction(self):
        source = 'def f(x):\n    if x:\n        print(x)\n    return x\n'
        cases = list(word_cases(source, 'fixture'))
        contexts = {case.id: prediction_context(case.prefix) for case in cases}
        for family, model_class in [('word', WordNGramModel), ('character', CharacterNGramModel)]:
            for n in range(1, 11):
                with self.subTest(family=family, n=n):
                    model = model_class(n)
                    model.fit([source, 'elsewhere = example()\n'])
                    cached = cached_ranker(model, family, contexts)
                    for case in cases:
                        self.assertEqual(list(cached(case)), model.suggest(case.prefix))


if __name__ == '__main__':
    unittest.main()
