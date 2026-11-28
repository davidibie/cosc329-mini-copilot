import contextlib
import io
import tempfile
import threading
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from editor import Editor, FakePredictor, main
from ngram_models import CharacterNGramModel, WordNGramModel


class EditorLaunchTests(unittest.TestCase):
    def test_loads_one_saved_model_and_wraps_it_before_starting_the_editor(self):
        for family, model_type in (("word", WordNGramModel), ("character", CharacterNGramModel)):
            with self.subTest(family=family), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "model.json"
                model = model_type(2)
                model.fit(["print(value)\n"])
                model.save(path)
                with patch("editor.tk.Tk") as window, patch("editor.Editor") as editor:
                    main(["--model", str(path), "--family", family,
                          "--ast-weight", "0.5", "--pool-size", "10"])
                loaded = editor.call_args.args[1]
                label, hybrid = editor.call_args.kwargs["alternative"]
                self.assertIsInstance(loaded, model_type)
                self.assertEqual(loaded.suggest("pri"), ["print"])
                self.assertEqual(label, "Hybrid")
                self.assertIs(hybrid.ngram, loaded)
                self.assertEqual((hybrid.ast_weight, hybrid.pool_size), (0.5, 10))
                window.return_value.mainloop.assert_called_once()

    def test_missing_model_reports_usage_error_before_opening_a_window(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.json"
            stderr = io.StringIO()
            with (patch("editor.tk.Tk") as window, contextlib.redirect_stderr(stderr),
                  self.assertRaises(SystemExit) as error):
                main(["--model", str(missing)])
        self.assertEqual(error.exception.code, 2)
        self.assertIn("Could not start model comparison", stderr.getvalue())
        window.assert_not_called()


class InFlightPredictor:
    def __init__(self, blocked_prefix, responses):
        self.blocked_prefix = blocked_prefix
        self.responses = responses
        self.started = threading.Event()
        self.release = threading.Event()

    def suggest(self, prefix, limit=5):
        if prefix == self.blocked_prefix:
            self.started.set()
            if not self.release.wait(timeout=4):
                raise TimeoutError("Test did not release the in-flight prediction")
        return self.responses.get(prefix, [])[:limit]


class EditorWidgetTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"Tk window is unavailable: {error}")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)

    def wait_for(self, condition):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            self.root.update()
            if condition():
                return
            time.sleep(0.005)
        self.fail("Timed out waiting for the editor")

    def set_code(self, editor, text, cursor):
        editor.text.replace("1.0", "end-1c", text)
        editor.text.mark_set("insert", cursor)
        editor.queue_update()

    def suggestions(self, editor):
        return [child.cget("text") for child in editor.suggestions.winfo_children()]

    def test_switch_keeps_the_ui_responsive_and_discards_the_old_model_result(self):
        original = InFlightPredictor("pri", {"pri": ["private"]})
        self.addCleanup(original.release.set)
        editor = Editor(self.root, original, model_name="N-gram", alternative=("Hybrid", FakePredictor()))
        self.set_code(editor, "pri", "1.3")
        self.wait_for(original.started.is_set)

        heartbeat = threading.Event()
        self.root.after(0, heartbeat.set)
        editor.model_name.set("Hybrid")
        self.wait_for(heartbeat.is_set)
        self.assertFalse(original.release.is_set())
        self.assertEqual(self.suggestions(editor), [])

        original.release.set()
        self.wait_for(lambda: bool(self.suggestions(editor)))
        self.assertEqual(self.suggestions(editor), ["print"])

    def test_cursor_move_discards_the_old_prefix_and_only_sends_visible_code(self):
        predictor = InFlightPredictor("pri", {"pri": ["private"], "pri\nret": ["return"]})
        self.addCleanup(predictor.release.set)
        editor = Editor(self.root, predictor)
        self.set_code(editor, "pri\nret extra", "1.3")
        self.wait_for(predictor.started.is_set)

        editor.text.mark_set("insert", "2.3")
        editor.queue_update()
        predictor.release.set()
        self.wait_for(lambda: bool(self.suggestions(editor)))
        self.assertEqual(self.suggestions(editor), ["return"])

    def test_failure_clears_suggestions_and_the_next_edit_can_recover(self):
        class Predictor:
            def suggest(self, prefix, limit=5):
                if prefix == "bad":
                    raise SyntaxError("test parser failure")
                return ["print"] if prefix == "pri" else []

        editor = Editor(self.root, Predictor())
        self.set_code(editor, "bad", "1.3")
        with self.assertLogs("editor", level="ERROR"):
            self.wait_for(lambda: editor.status.cget("text").startswith("Suggestions unavailable"))
        self.assertEqual(self.suggestions(editor), [])

        self.set_code(editor, "pri", "1.3")
        self.wait_for(lambda: self.suggestions(editor) == ["print"])
        self.set_code(editor, "zzz", "1.3")
        self.wait_for(lambda: editor.status.cget("text") == "No suggestions")
        self.assertEqual(self.suggestions(editor), [])

    def test_accepting_a_suggestion_replaces_whole_identifier_and_can_be_undone(self):
        editor = Editor(self.root, FakePredictor())
        self.set_code(editor, "printrange + value", "1.3")
        self.wait_for(lambda: self.suggestions(editor) == ["print"])
        editor.suggestions.winfo_children()[0].invoke()
        self.assertEqual(editor.text.get("1.0", "end-1c"), "print + value")
        self.assertEqual(editor.text.index("insert"), "1.5")
        editor.text.edit_undo()
        self.assertEqual(editor.text.get("1.0", "end-1c"), "printrange + value")


if __name__ == "__main__":
    unittest.main()
