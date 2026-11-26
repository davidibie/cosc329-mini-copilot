# Parsing incomplete Python (T08)

Use Python's `ast` when the prefix with a cursor placeholder parses and Parso 0.8.6 with the Python 3.12 grammar for recovery. Parso preserved the order and spelling of tokens in the unfinished cases and recovered a complete call after a malformed line. See the [AST predictor](AST_PREDICTOR.md) for the implemented classification and fallback rules.

## Reproduce the comparison

Run these commands from the repository root with Python 3.12 in an activated virtual environment. Tree-sitter is only needed for this comparison.

```sh
python -m pip install parso==0.8.6 tree-sitter==0.25.2 tree-sitter-python==0.25.0
python scripts/compare_parsers.py
```

## Observations

These results were observed on Python 3.12.14 with the versions above. A trailing `\n` in the table represents a newline.

| Prefix | Python `ast` | Parso | Tree-sitter |
| --- | --- | --- | --- |
| `def greet(` | Syntax error | `error_node` retains `def`, `greet` and `(` | `ERROR` |
| `values = [item` | Syntax error | `error_node` retains the target, `=` and `[` | `ERROR` |
| `print(value` | Syntax error | `error_node` retains the function, `(` and argument | `ERROR` |
| `total =` | Syntax error | `error_node` retains the target and `=` | `ERROR` |
| `pri` | A `Name` expression | A `name` leaf, no error | An `identifier`, no error |
| `def greet():\n` | Expected an indented block | `error_node` with a `parameters` child and an indentation diagnostic | Function with an empty block, `has_error=False` |
| Empty input | Empty module | An end marker, no error | Empty module |
| `total =\nprint(value)` | Syntax error | Assignment error followed by a separate call | Assignment with the call as its right side, `has_error=False` |
| `total = sum(values)` | `Assign` containing a `Call` | `expr_stmt` with an `atom_expr` and a call trailer | Assignment containing a call |

## Use in the predictor

- In a temporary copy of the visible prefix, put a placeholder at the cursor and run `ast.parse`. Read abstract nodes such as `FunctionDef`, `Assign`, `Import`, and `Attribute` when available.
- On `SyntaxError`, parse the same probe with Parso in recovery mode. Parso returns a concrete syntax tree with typed nodes, token leaves, and source positions. It can group unfinished syntax in `error_node` and represent unexpected tokens with `error_leaf`. Use the closest relevant node and its recovered tokens to infer the cursor context. A partial identifier can be valid Python, so derive its spelling from the cursor position independently of parse errors.
- Map recognized Parso nodes and recovered token patterns to the same abstract contexts used for the Python AST. For example, a name followed by a call trailer or a recovered opening parenthesis can indicate a call. An incomplete `def` header provides function context. Keep the nearest relevant node and avoid inferring a specific context from an unrelated earlier statement.
- When the parser cannot recover enough structure near the cursor, record a fallback and use context-neutral candidates subject to the partial-word filter. Return fewer than five, including zero, when too few candidates qualify. The full-prefix parse provides structural context and classification. A syntax error elsewhere in the prefix should not automatically disqualify a completion.

[Python AST](https://docs.python.org/3.12/library/ast.html) · [Parso recovery](https://parso.readthedocs.io/en/latest/docs/usage.html) · [Parso tree types](https://parso.readthedocs.io/en/latest/docs/parser-tree.html) · [Tree-sitter error and missing nodes](https://tree-sitter.github.io/tree-sitter/using-parsers/queries/1-syntax.html)
