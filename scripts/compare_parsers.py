"""Compare parser recovery on prefixes that occur while typing Python."""

import ast
from importlib.metadata import version
import sys

import parso
from tree_sitter import Language, Parser
import tree_sitter_python


PREFIXES = {
    "Unfinished function definition": "def greet(",
    "Unclosed bracket": "values = [item",
    "Unclosed call": "print(value",
    "Incomplete assignment": "total =",
    "Partial identifier": "pri",
    "Function waiting for a body": "def greet():\n",
    "Empty input": "",
    "Invalid line followed by a valid call": "total =\nprint(value)",
    "Complete assignment and call": "total = sum(values)",
}


def describe_parso(node):
    if hasattr(node, "children"):
        return (node.type, [describe_parso(child) for child in node.children])
    return (node.type, node.value)


def main():
    print(f"Python {sys.version.split()[0]}")
    for package in ("parso", "tree-sitter", "tree-sitter-python"):
        print(f"{package} {version(package)}")

    grammar = parso.load_grammar(version="3.12")
    parser = Parser(Language(tree_sitter_python.language()))
    for label, prefix in PREFIXES.items():
        print(f"\n{label}: {prefix!r}")
        try:
            print("Python AST:", ast.dump(ast.parse(prefix)))
        except SyntaxError as error:
            print("Python AST:", error.msg)

        module = grammar.parse(prefix, error_recovery=True)
        print("Parso:", describe_parso(module))
        print("Parso errors:", [error.message for error in grammar.iter_errors(module)])

        root = parser.parse(prefix.encode("utf-8")).root_node
        print(f"Tree-sitter: {root} (has_error={root.has_error})")


if __name__ == "__main__":
    main()
