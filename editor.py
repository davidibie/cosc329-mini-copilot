"""A small Python editor for trying the Mini-Copilot prediction interface."""

import argparse
import logging
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from tkinter import ttk

from text_processing import identifier_suffix, is_identifier_character, partial_word


_SUGGESTION_LIMIT = 5
_DEBOUNCE_MS = 60
_POLL_MS = 20
_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Request:
    model_name: str
    prefix: str
    blocked: bool


class FakePredictor:
    """Use a fixed vocabulary so the editor can run without trained models."""

    words = ("print", "return", "import", "len", "range", "list", "enumerate", "pass", "property")

    def suggest(self, prefix: str, limit: int = 5) -> list[str]:
        partial = partial_word(prefix)
        if partial is None or limit <= 0:
            return []
        return [word for word in self.words if word.startswith(partial) and word != partial][:limit]


class Editor:
    def __init__(self, root: tk.Tk, predictor, *, model_name="Demo", alternative=None):
        self.root = root
        self.models = {model_name: predictor}
        if alternative is not None:
            name, predictor = alternative
            self.models[name] = predictor
        self.model_name = tk.StringVar(master=root, value=model_name)
        self._demo = alternative is None and isinstance(self.models[model_name], FakePredictor)
        self._request = None
        self._displayed_request = None
        self._update_id = None
        self._poll_id = None
        self._future = None
        self._closed = False
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="copilot-predictor")

        root.title("Mini-Copilot")
        root.minsize(550, 260)
        container = ttk.Frame(root, padding=12)
        container.pack(fill="both", expand=True)

        if alternative is not None:
            controls = ttk.Frame(container)
            controls.pack(fill="x", pady=(0, 8))
            ttk.Label(controls, text="Model").pack(side="left", padx=(0, 8))
            ttk.Combobox(controls, textvariable=self.model_name, values=tuple(self.models),
                         state="readonly", width=24).pack(side="left")
            self.model_name.trace_add("write", self.queue_update)

        self.text = tk.Text(container, font="TkFixedFont", undo=True, wrap="none", padx=8, pady=8)
        self.text.pack(fill="both", expand=True)
        self.status = ttk.Label(container)
        self.status.pack(anchor="w", pady=(10, 4))
        self.suggestions = ttk.Frame(container)
        self.suggestions.pack(fill="x")

        self.text.bind("<<Modified>>", self.on_text_modified)
        self.text.bind("<KeyRelease>", self.queue_update)
        self.text.bind("<ButtonRelease-1>", self.queue_update)
        root.bind("<Destroy>", self._on_destroy, add="+")
        self.text.focus_set()
        self.queue_update()

    def on_text_modified(self, _event):
        if self.text.edit_modified():
            self.text.edit_modified(False)
            self.queue_update()

    def _current_request(self):
        prefix = self.text.get("1.0", "insert")
        right_character = self.text.get("insert", "insert + 1 chars")
        blocked = not identifier_suffix(prefix) and is_identifier_character(right_character)
        return _Request(self.model_name.get(), prefix, blocked)

    def queue_update(self, *_event):
        if self._closed:
            return
        request = self._current_request()
        if request == self._request:
            return

        self._request = request
        self._cancel_prediction()
        if request.blocked:
            self._show_suggestions(request, [])
        else:
            self._clear_suggestions("Updating suggestions…")
            self._update_id = self.root.after(_DEBOUNCE_MS, self._start_prediction)

    def _start_prediction(self):
        self._update_id = None
        request = self._request
        predictor = self.models[request.model_name]
        self._future = self._executor.submit(predictor.suggest, request.prefix, limit=_SUGGESTION_LIMIT)
        self._poll_prediction()

    def _poll_prediction(self):
        self._poll_id = None
        if not self._future.done():
            self._poll_id = self.root.after(_POLL_MS, self._poll_prediction)
            return

        future, self._future = self._future, None
        request = self._request
        if request != self._current_request():
            self.queue_update()
            return
        try:
            words = future.result()
        except Exception:
            _LOGGER.exception("Prediction failed")
            self._clear_suggestions("Suggestions unavailable. Edit or switch models to retry.")
        else:
            self._show_suggestions(request, words)

    def _cancel_prediction(self):
        for callback in (self._update_id, self._poll_id):
            if callback is not None:
                self.root.after_cancel(callback)
        self._update_id = self._poll_id = None
        if self._future is not None:
            self._future.cancel()
            self._future = None

    def _on_destroy(self, event):
        if event.widget is self.root:
            self._closed = True
            self._cancel_prediction()
            self._executor.shutdown(wait=False, cancel_futures=True)

    def _clear_suggestions(self, status):
        self._displayed_request = None
        self.status.configure(text=status)
        for button in self.suggestions.winfo_children():
            button.destroy()

    def _show_suggestions(self, request, words):
        label = "demo suggestions" if self._demo else "suggestions"
        self._clear_suggestions(label.capitalize() if words else f"No {label}")
        self._displayed_request = request
        for word in words[:_SUGGESTION_LIMIT]:
            button = ttk.Button(self.suggestions, text=word,
                                command=lambda word=word: self.accept(word, request))
            button.pack(side="left", padx=(0, 4))

    def accept(self, word: str, request=None):
        displayed = self._displayed_request
        if (displayed is None or displayed != self._current_request()
                or (request is not None and request != displayed)):
            self.queue_update()
            return

        partial = partial_word(displayed.prefix)
        if partial is None:
            return

        right = self.text.get("insert", "insert lineend")
        suffix_length = 0
        for character in right:
            if not is_identifier_character(character):
                break
            suffix_length += 1
        if suffix_length and not partial:
            self.queue_update()
            return

        start = self.text.index(f"insert - {len(partial)} chars")
        end = f"insert + {suffix_length} chars"
        self.text.edit_separator()
        self.text.replace(start, end, word)
        self.text.edit_separator()
        self.text.mark_set("insert", f"{start} + {len(word)} chars")
        self.text.see("insert")
        self.text.focus_set()
        self.queue_update()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, help="Trained n-gram JSON for the model comparison")
    parser.add_argument("--family", choices=("word", "character"), default="word")
    parser.add_argument("--pool-size", type=int, default=25, help="Size of the hybrid candidate pool")
    parser.add_argument("--ast-weight", type=float, default=0.75, help="Weight given to AST agreement")
    args = parser.parse_args(argv)

    if args.model is None:
        root = tk.Tk()
        Editor(root, FakePredictor())
        root.mainloop()
        return

    try:
        from hybrid_predictor import HybridPredictor
        from ngram_models import CharacterNGramModel, WordNGramModel
    except ModuleNotFoundError as error:
        parser.error(f"{error}. Install requirements.txt to use trained models.")

    model_class = WordNGramModel if args.family == "word" else CharacterNGramModel
    try:
        model = model_class.load(args.model)
        hybrid = HybridPredictor(model, pool_size=args.pool_size, ast_weight=args.ast_weight)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        parser.error(f"Could not start model comparison with {args.model}: {error}")

    root = tk.Tk()
    Editor(root, model, model_name=f"{args.family.capitalize()} {model.n}-gram",
           alternative=("Hybrid", hybrid))
    root.mainloop()


if __name__ == "__main__":
    main()
