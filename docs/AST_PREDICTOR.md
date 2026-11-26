# Syntax-aware prediction baseline (T09)

The baseline uses rules and visible Python names. It requires no training corpus or saved model. Use `ASTPredictor.suggest` in the shared evaluator alongside the two n-gram models. The predictor takes only the text before the cursor and never imports or executes that text.

## Run it

Use Python 3.12 from the repository root, preferably in a virtual environment.

```sh
python -m pip install -r requirements.txt
python -c "from ast_predictor import ASTPredictor; model = ASTPredictor(); print(model.suggest('from math import sq')); print(model.predict('call(pri'))"
python -m unittest discover -s tests -v
```

The first prediction returns `['sqrt']`. The second returns `print` with `context='call'` and `parser='parso'` because the call is still open.

## Infer where the next word goes

1. Use the shared lexical guard to read the partial word and completed names. Hide suggestions inside a comment, string or f-string, or when the guard disallows appending a word to a number.
2. Replace the partial in a temporary copy of the prefix with a placeholder name. Parse that copy with `ast.parse` using Python 3.12 grammar. Inspect the AST node and parents that end at the placeholder. An assignment value is an expression, an `Attribute` gives a member name, and an `Import` or `ImportFrom` gives an import slot. At the start of a statement, distinguish function bodies so `return` and `yield` appear only in that context. A cursor waiting for required indentation receives no suggestions until the indentation is present.
3. If the AST rejects the probe, use Parso recovery. Locate the placeholder by its source position in the concrete tree. Map the closest relevant node or recovered tokens to the same set of abstract contexts. For example, the closest unfinished call can retain its opening parenthesis and arguments, while a recovered function header distinguishes parameters from default values. See [parser comparison](PARSER_INVESTIGATION.md).

## Rank and check candidates

Use context-specific words first where available. The rules use statement starters, common parameter names, common member names, and a small set of standard-library modules and exports. The expression and call rules use visible identifiers, a small set of built-ins, and `False`, `None`, and `True`. The visible-name tier considers up to 64 recent distinct completed identifiers from the prefix, regardless of scope. These names preserve their original spelling. Sort words lexicographically within each tier, remove duplicates, and require case-sensitive strict extension of a partial. Return up to the requested limit.

Check each word by parsing a short complete Python example for its inferred slot. An attribute completion goes in `example.<word>`, for example, and a parameter goes in `def example(<word>): pass`. Statement keywords use a short skeleton that supplies required punctuation and a body. A function statement is checked inside a function. This checks the candidate's grammatical role while allowing the real prefix to contain unfinished or unrelated invalid syntax. The placeholder and skeleton are only used for analysis. The predictor returns the full word without punctuation.

## Diagnostics and limits

`ASTPredictor.predict(prefix, limit=5)` returns the same words as an immutable tuple, plus `context`, `parser`, and `used_fallback`. `parser` is `ast` or `parso` when a parser was attempted and `None` when the lexical guard suppressed the input or the limit was nonpositive. `used_fallback=True` identifies a switch to context-neutral expression candidates when neither parser can classify the cursor. Parso can recover a specific context without using that fallback. Empty suggestions can be counted separately using the returned words.

The grammar check cannot confirm that a visible name is in scope or that an object has a proposed member. The rules cover common syntactic contexts and use a limited set of built-ins and imports. Unusual or ambiguous prefixes can produce generic suggestions or no match. Formal accuracy and edit-distance measurements belong to T12 and use the shared evaluation cases.
