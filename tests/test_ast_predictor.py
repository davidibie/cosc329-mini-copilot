import unittest

from ast_predictor import ASTPredictor


class ASTPredictorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = ASTPredictor()

    def test_ast_uses_cursor_structure_and_visible_spelling(self):
        cases = {
            'pri': ('statement', ['print']),
            'café = 5; result = ca': ('expression', ['café']),
            'items.ap': ('attribute', ['append']),
            'import pa': ('module', ['pathlib']),
            'from math import sq': ('import_name', ['sqrt']),
            'def greet():\n    re': ('function_statement', ['return']),
        }
        for prefix, (context, expected) in cases.items():
            with self.subTest(prefix=prefix):
                result = self.model.predict(prefix)
                self.assertEqual((result.parser, result.context), ('ast', context))
                self.assertEqual(list(result.suggestions), expected)
                self.assertFalse(result.used_fallback)

    def test_parso_recovers_the_cursor_context(self):
        cases = {
            'value = [pri': ('expression', 'print'),
            'old =\ncall(pri': ('call', 'print'),
            'call(items.ap': ('attribute', 'append'),
            'from math i': ('import_keyword', 'import'),
            'old =\nfrom math import sq': ('import_name', 'sqrt'),
            'def greet(se': ('parameters', 'self'),
            'async def greet(se': ('parameters', 'self'),
            'def greet(x = No': ('expression', 'None'),
            'def greet(x: st': ('expression', 'str'),
        }
        for prefix, (context, expected) in cases.items():
            with self.subTest(prefix=prefix):
                result = self.model.predict(prefix)
                self.assertEqual((result.parser, result.context), ('parso', context))
                self.assertEqual(result.suggestions, (expected,))
                self.assertFalse(result.used_fallback)

    def test_fallback_is_reported_without_using_the_earlier_assignment(self):
        result = self.model.predict('broken =\npri')
        self.assertEqual((result.parser, result.context), ('parso', 'neutral'))
        self.assertTrue(result.used_fallback)
        self.assertEqual(result.suggestions, ('print',))

    def test_words_respect_the_inferred_syntax_slot(self):
        self.assertEqual(self.model.suggest('value = No'), ['None'])
        self.assertEqual(self.model.suggest('value.re'), [])
        self.assertEqual(self.model.suggest('def greet():\n    class Example:\n        re'), [])
        unindented = self.model.predict('def greet():\n')
        self.assertEqual((unindented.context, unindented.suggestions), ('awaiting_indent', ()))

    def test_shared_lexical_guard_suppresses_non_code(self):
        for prefix in ('# pri', 'value = "pri', 'f"{pri', 'value = 12pri'):
            with self.subTest(prefix=prefix):
                result = self.model.predict(prefix)
                self.assertEqual((result.parser, result.context), (None, 'suppressed'))
                self.assertEqual(result.suggestions, ())

    def test_ranking_and_empty_output_follow_the_shared_contract(self):
        self.assertEqual(len(self.model.suggest('')), 5)
        self.assertEqual(self.model.suggest('', 3), ['class', 'def', 'for'])
        self.assertEqual(self.model.suggest('pri', 0), [])
        self.assertEqual(self.model.suggest('pri', -1), [])
        self.assertEqual(self.model.suggest('print'), [])
        self.assertEqual(self.model.suggest('Pri'), [])
        self.assertEqual(self.model.suggest('arg_b = 1\narg_a = 2\ncall(ar'), ['arg_a', 'arg_b'])
        suggestions = self.model.suggest('print = 1\nresult = pri', 10)
        self.assertEqual(suggestions, ['print'])


if __name__ == '__main__':
    unittest.main()
