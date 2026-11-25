"""A small Python editor for trying the Mini-Copilot prediction interface."""

import tkinter as tk
from tkinter import ttk

from text_processing import identifier_suffix, is_identifier_character, partial_word


class FakePredictor:
    """Use a fixed vocabulary so the editor can run without trained models."""

    words = ("print", "return", "import", "len", "range", "list", "enumerate", "pass", "property")

    def suggest(self, prefix: str, limit: int = 5) -> list[str]:
        partial = partial_word(prefix)
        if partial is None or limit <= 0:
            return []
        return [word for word in self.words if word.startswith(partial) and word != partial][:limit]


class Editor:
    def __init__(self, root: tk.Tk, predictor):
        self.root = root
        self.predictor = predictor
        self.displayed_prefix = None
        self.pending_update = None

        root.title("Mini-Copilot")
        root.minsize(550, 260)
        container = ttk.Frame(root, padding=12)
        container.pack(fill="both", expand=True)

        self.text = tk.Text(container, font="TkFixedFont", undo=True, wrap="none", padx=8, pady=8)
        self.text.pack(fill="both", expand=True)
        self.status = ttk.Label(container)
        self.status.pack(anchor="w", pady=(10, 4))
        self.suggestions = ttk.Frame(container)
        self.suggestions.pack(fill="x")

        self.text.bind("<<Modified>>", self.on_text_modified)
        self.text.bind("<KeyRelease>", self.queue_update)
        self.text.bind("<ButtonRelease-1>", self.queue_update)
        self.text.focus_set()
        self.update_suggestions()

    def on_text_modified(self, _event):
        if self.text.edit_modified():
            self.text.edit_modified(False)
            self.queue_update()

    def queue_update(self, _event=None):
        if self.pending_update is None:
            self.pending_update = self.root.after_idle(self.update_suggestions)

    def update_suggestions(self):
        self.pending_update = None
        for button in self.suggestions.winfo_children():
            button.destroy()

        prefix = self.text.get("1.0", "insert")
        right_character = self.text.get("insert", "insert + 1 chars")
        words = []
        if identifier_suffix(prefix) or not is_identifier_character(right_character):
            words = self.predictor.suggest(prefix, limit=5)

        self.displayed_prefix = prefix
        self.status.configure(text="Demo suggestions" if words else "No demo suggestions")
        for word in words:
            button = ttk.Button(self.suggestions, text=word, command=lambda word=word: self.accept(word))
            button.pack(side="left", padx=(0, 4))

    def accept(self, word: str):
        prefix = self.text.get("1.0", "insert")
        if prefix != self.displayed_prefix:
            self.queue_update()
            return

        partial = partial_word(prefix)
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


def main():
    root = tk.Tk()
    Editor(root, FakePredictor())
    root.mainloop()


if __name__ == "__main__":
    main()
