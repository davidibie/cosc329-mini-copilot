import unittest
from unittest.mock import Mock

from hybrid_predictor import HybridPredictor
from ngram_models import CharacterNGramModel, WordNGramModel


class HybridPredictorTests(unittest.TestCase):
    def test_context_can_promote_a_candidate_outside_the_first_five(self):
        ngram = Mock()
        ngram.suggest.return_value = ['private', 'priority', 'primitive', 'prism', 'primal', 'print']
        model = HybridPredictor(ngram)

        result = model.predict('call(pri')

        ngram.suggest.assert_called_once_with('call(pri', 25)
        self.assertEqual(result.suggestions, ('private', 'print', 'priority', 'primitive', 'prism'))
        self.assertEqual((result.context, result.parser), ('call', 'parso'))
        self.assertFalse(result.used_fallback)

    def test_ties_use_lexical_order_and_zero_weight_preserves_ngram_order(self):
        ngram = Mock()
        ngram.suggest.return_value = ['priority', 'print']

        self.assertEqual(HybridPredictor(ngram, ast_weight=0.5).suggest('pri'), ['print', 'priority'])
        self.assertEqual(HybridPredictor(ngram, ast_weight=0).suggest('pri'), ['priority', 'print'])

    def test_fallbacks_keep_ngram_order_and_report_why(self):
        ngram = Mock()
        ngram.suggest.return_value = ['private', 'priority']
        model = HybridPredictor(ngram)
        cases = {
            'broken =\npri': 'ast_context_unavailable',
            'def pri': 'no_ast_candidates',
            'pri': 'no_overlap',
        }
        for prefix, reason in cases.items():
            with self.subTest(prefix=prefix):
                result = model.predict(prefix, 1)
                self.assertEqual(result.suggestions, ('private',))
                self.assertEqual(result.fallback_reason, reason)
                self.assertTrue(result.used_fallback)

    def test_empty_pool_and_nonpositive_limit_return_no_suggestions(self):
        ngram = Mock()
        ngram.suggest.return_value = []
        model = HybridPredictor(ngram, pool_size=1)
        self.assertEqual(model.suggest('from math import sq', 0), [])
        ngram.suggest.assert_not_called()

        result = model.predict('from math import sq', 5)
        ngram.suggest.assert_called_once_with('from math import sq', 5)
        self.assertEqual(result.suggestions, ())
        self.assertIsNone(result.parser)

    def test_both_trained_families_follow_the_shared_interface(self):
        for family in (WordNGramModel, CharacterNGramModel):
            with self.subTest(family=family.__name__):
                ngram = family(2)
                ngram.fit(['private = 1\nprint(private)\n'])
                hybrid = HybridPredictor(ngram)
                self.assertCountEqual(hybrid.suggest('pri'), ['print', 'private'])
                self.assertEqual(hybrid.suggest('# pri'), [])
                self.assertEqual(hybrid.suggest('Pri'), [])

    def test_rejects_invalid_configuration(self):
        for value in (False, 0, -1, 2.5):
            with self.subTest(pool_size=value), self.assertRaises(ValueError):
                HybridPredictor(Mock(), pool_size=value)
        for value in (-1, float('nan'), float('inf')):
            with self.subTest(ast_weight=value), self.assertRaises(ValueError):
                HybridPredictor(Mock(), ast_weight=value)


if __name__ == '__main__':
    unittest.main()
