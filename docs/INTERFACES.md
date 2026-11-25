# Prediction interface (T02)

**Status:** Proposal for David and Kamso to review. Python is the implementation and dataset language. David owns the dataset, n-grams and shared evaluator; Kamso owns the parser, AST model, hybrid and editor. See [PLAN.md](PLAN.md) for the full work split.

## Model calls

- `fit(source_strings: Iterable[str]) -> None` trains a model from whole Python source files and replaces any previous fitted state. Fit only models that learn from data. Supply only files in the active training split and reset context at file boundaries.
- `suggest(prefix: str, limit: int = 5) -> list[str]` takes all the text before the cursor, including any partial word. Pass the prefix as written, with whitespace and case preserved. Never supply the remainder of the file or a hidden target word.
- Return up to `limit` distinct, full words, best first. For a nonempty partial, candidates must case-sensitively start with it and be longer than it. Break ties by Python's string sort order. Return `[]` for a nonpositive limit or when no candidate qualifies. The editor asks for five; the hybrid may ask for a larger pool. Ranking scores are internal to each model.

## Words and cursor behavior

- Identify targets in complete Python 3.12 source with `tokenize`: use the original spelling of `NAME` tokens, which cover identifiers and keywords. Exclude comments, string literals (including f-strings and their interpolations), numbers, operators, punctuation and whitespace from the target list. Model families can still use non-target syntax as context. Word-based components and the evaluator should share this target extraction.
- For a live prefix, find the trailing run of Python identifier characters and treat it as a partial only if the entire run is a valid identifier spelling. The input may be incomplete, so use recovery or a conservative fallback for lexical context. Suppress suggestions inside comments and strings and directly after a numeric token where a word would join that token.
- For `pri|`, accepting `print` replaces `pri`. For `pri|nt`, replace the whole identifier, including `nt` to the right. Only the editor inspects the right side to find the replacement range. If an identifier starts immediately to the right with no partial to the left, the editor hides suggestions to avoid overwriting it. At a word boundary with no adjacent word, insert at the cursor and leave surrounding spacing unchanged.

## Shared evaluation

- Use one full-word-boundary case per eligible held-out token. Place the cursor immediately before the token and keep the expected word inside the evaluator. If evaluating partially typed words, use a separately labeled set with the cursor after the first character of targets longer than one character. Reuse the same case IDs and prefixes across models.
- Report exact-match accuracy and character Levenshtein distance for the first suggestion. Count empty output as a miss and use the distance from `""` to the expected word. Log empty outputs and fallbacks so they can be interpreted alongside the metrics. If top-five accuracy is reported, label it separately.
- Reuse the project-level splits and case files. Build vocabularies and model statistics from the current training files, and save each fold's metrics before summarizing them.

## Model loading

Trainable models expose `save(path)` and a class method `load(path)` that reconstructs a predictor ready for `suggest`. Use versioned JSON containing the model type, configuration, and fitted state. Construct rules-only models directly. Load or construct the two editor predictors once at startup.
