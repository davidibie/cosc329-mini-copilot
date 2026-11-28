"""Rank Python completions with rules driven by the syntax before the cursor."""

import ast
import keyword
from dataclasses import dataclass
from functools import lru_cache
from itertools import islice

import parso
from parso.parser import ParserSyntaxError

from text_processing import prediction_context


_CURSOR = '__copilot_cursor__'
_PYTHON_VERSION = (3, 12)
_BUILTINS = ('abs', 'dict', 'enumerate', 'len', 'list', 'max', 'min', 'print',
             'range', 'set', 'str', 'sum', 'tuple', 'zip')
_LITERALS = ('False', 'None', 'True')
_METHODS = ('append', 'clear', 'copy', 'extend', 'get', 'items', 'keys', 'pop', 'update', 'values')
_IMPORTS = {
    'collections': ('Counter', 'defaultdict', 'deque'),
    'functools': ('cache', 'lru_cache', 'partial', 'reduce', 'wraps'),
    'itertools': ('chain', 'islice', 'product'),
    'json': ('dump', 'dumps', 'load', 'loads'),
    'math': ('ceil', 'floor', 'isfinite', 'pi', 'sqrt'),
    'os': ('environ', 'getcwd', 'path'),
    'pathlib': ('Path', 'PurePath'),
    're': ('compile', 'findall', 'match', 'search', 'sub'),
    'sys': ('argv', 'exit', 'stdin', 'stdout'),
    'typing': ('Any', 'Iterable', 'Iterator', 'Protocol'),
}
_STATEMENTS = {
    'class': 'class Example: pass',
    'def': 'def example(): pass',
    'for': 'for item in items: pass',
    'from': 'from example import item',
    'if': 'if True: pass',
    'import': 'import example',
    'pass': 'pass',
    'raise': 'raise Exception',
    'try': 'try: pass\nexcept Exception: pass',
    'while': 'while False: pass',
    'with': 'with resource: pass',
}
_FUNCTION_STATEMENTS = {'return': 'return None', 'yield': 'yield None'}
_OPENINGS = {'(', '[', '{'}
_SLOT_EXAMPLES = {
    'attribute': 'example.{}',
    'call': 'example({})',
    'identifier': '{} = None',
    'import_keyword': 'from example {} name',
    'import_name': 'from example import {}',
    'module': 'import {}',
    'parameters': 'def example({}): pass',
}


@dataclass(frozen=True)
class Prediction:
    suggestions: tuple[str, ...]
    context: str
    parser: str | None
    used_fallback: bool = False


@dataclass(frozen=True)
class _Slot:
    kind: str
    module: str | None = None


def _ast_slot(tree, end):
    """Find the node ending at the placeholder and classify its parent chain."""
    path = [tree]
    while True:
        match = next((child for child in ast.iter_child_nodes(path[-1])
                      if (getattr(child, 'end_lineno', None),
                          getattr(child, 'end_col_offset', None)) == end), None)
        if match is None:
            break
        path.append(match)

    node = path[-1]
    if isinstance(node, ast.alias):
        parent = path[-2]
        if node.asname == _CURSOR:
            return _Slot('identifier')
        if isinstance(parent, ast.ImportFrom):
            return _Slot('import_name', parent.module if parent.level == 0 else None)
        return _Slot('module')
    if isinstance(node, ast.Attribute) and node.attr == _CURSOR:
        return _Slot('attribute')
    if isinstance(node, ast.Name) and node.id == _CURSOR:
        if isinstance(path[-2], ast.Expr):
            scope = next((item for item in reversed(path) if isinstance(
                item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))), None)
            in_function = isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef))
            return _Slot('function_statement' if in_function else 'statement')
        return _Slot('call' if isinstance(path[-2], ast.Call) else 'expression')
    if isinstance(node, ast.arg) and node.arg == _CURSOR:
        return _Slot('parameters')
    return None


def _import_slot(words):
    if words[-1] == 'as':
        return _Slot('identifier')
    if words[0] == 'import':
        return _Slot('module')
    if 'import' in words:
        return _Slot('import_name', ''.join(words[1:words.index('import')]))
    return _Slot('import_keyword' if len(words) > 1 and words[-1] != '.' else 'module')


def _words_before(node, leaf):
    words = []
    current = node.get_first_leaf()
    while current is not None and current is not leaf and current.end_pos <= leaf.start_pos:
        if current.type != 'newline':
            words.append(current.value)
        current = current.get_next_leaf()
    return words


def _error_slot(node, leaf):
    """Use recovered tokens from the closest incomplete grammar node."""
    children = node.children
    words = _words_before(node, leaf)
    if not words:
        return None
    if words[:2] == ['async', 'def']:
        words = words[1:]
    if words[0] in {'from', 'import'}:
        return _import_slot(words)
    if words[0] in {'def', 'class'} and len(words) == 1:
        return _Slot('identifier')
    if words[0] == 'for' and 'in' not in words:
        return _Slot('identifier')
    if words[-1] == '.':
        return _Slot('attribute')
    if words[0] == 'def' and '->' in words:
        return _Slot('expression')
    parameter_opening = next((child for child in children if getattr(child, 'value', None) == '('), None)
    for index in range(len(children) - 1, -1, -1):
        child = children[index]
        opening = getattr(child, 'value', None)
        if opening in _OPENINGS:
            if words[0] == 'def' and child is parameter_opening:
                return _Slot('expression' if '=' in words else 'parameters')
            preceding = children[index - 1] if index else None
            if opening == '(' and getattr(preceding, 'type', None) in {'name', 'trailer', 'atom_expr'}:
                return _Slot('call')
            return _Slot('expression')
    if '=' in words or words[0] in {'if', 'elif', 'while', 'with', 'assert', 'return', 'raise', 'yield', 'for'}:
        return _Slot('expression')
    return None


def _parso_slot(tree, position):
    leaf = tree.get_leaf_for_position(position)
    if leaf is None or leaf.value != _CURSOR:
        return None
    node = leaf.parent
    while node is not None:
        if node.type == 'trailer' and node.get_first_leaf().value == '.':
            return _Slot('attribute')
        if node.type == 'arglist':
            return _Slot('call')
        if node.type in {'import_name', 'import_from'}:
            return _import_slot(_words_before(node, leaf))
        if node.type in {'expr_stmt', 'return_stmt', 'raise_stmt', 'tfpdef'}:
            return _Slot('expression')
        if node.type == 'typedargslist':
            separator = next((part.value for part in reversed(node.children)
                              if getattr(part, 'value', None) in {'=', ','}), None)
            return _Slot('expression' if separator == '=' else 'parameters')
        if node.type == 'error_node':
            return _error_slot(node, leaf)
        node = node.parent

    # Parso may put the placeholder after a separate error node in `from module `.
    previous = leaf.get_previous_leaf()
    if previous is not None and previous.end_pos[0] == leaf.start_pos[0]:
        error = previous.parent
        while error is not None and error.type != 'error_node':
            error = error.parent
        if error is not None and error.get_first_leaf().value in {'from', 'import'}:
            return _error_slot(error, leaf)
    return None


def _candidate_groups(slot, names):
    if slot.kind == 'module':
        return (_IMPORTS, names)
    if slot.kind == 'import_name':
        return (_IMPORTS.get(slot.module, ()), names)
    if slot.kind == 'import_keyword':
        return (('import',),)
    if slot.kind == 'attribute':
        return (_METHODS, names)
    if slot.kind == 'parameters':
        return (('args', 'kwargs', 'self', 'value'), names)
    if slot.kind == 'identifier':
        return (names,)
    if slot.kind == 'function_statement':
        return (_FUNCTION_STATEMENTS, _STATEMENTS, names, _BUILTINS)
    if slot.kind == 'statement':
        return (_STATEMENTS, names, _BUILTINS)
    return (names, _BUILTINS, _LITERALS)


@lru_cache(maxsize=2048)
def _fits_slot(kind, word):
    """Check one word in a small, complete example of the inferred grammar slot."""
    if not word.isidentifier():
        return False
    if kind in {'statement', 'function_statement'}:
        snippet = _STATEMENTS.get(word, word)
        if kind == 'function_statement':
            snippet = _FUNCTION_STATEMENTS.get(word, snippet)
            snippet = 'def example():\n    ' + snippet.replace('\n', '\n    ')
    else:
        snippet = _SLOT_EXAMPLES.get(kind, 'value = {}').format(word)
    try:
        ast.parse(snippet, feature_version=_PYTHON_VERSION)
        return True
    except SyntaxError:
        return False


class ASTPredictor:
    """A rules-only predictor. No corpus fitting or future text is required."""

    def __init__(self):
        self._grammar = parso.load_grammar(version='3.12')

    def suggest(self, prefix: str, limit: int = 5) -> list[str]:
        return list(self.predict(prefix, limit).suggestions)

    def predict(self, prefix: str, limit: int = 5) -> Prediction:
        """Return suggestions with parser and fallback information for evaluation."""
        if limit <= 0:
            return Prediction((), 'disabled', None)
        context = prediction_context(prefix)
        if context is None:
            return Prediction((), 'suppressed', None)
        names, partial = context
        before = prefix[:-len(partial)] if partial else prefix
        probe = before + _CURSOR
        line = before.count('\n') + 1
        last_line = before.rpartition('\n')[2]
        parser = 'ast'
        try:
            tree = ast.parse(probe, feature_version=_PYTHON_VERSION)
        except (SyntaxError, RecursionError) as error:
            if (isinstance(error, IndentationError) and error.lineno == line
                    and error.msg.startswith('expected an indented block')):
                return Prediction((), 'awaiting_indent', 'ast')
            parser = 'parso'
            try:
                tree = self._grammar.parse(probe, error_recovery=True)
                slot = _parso_slot(tree, (line, len(last_line) + len(_CURSOR) - 1))
            except (ParserSyntaxError, RecursionError):
                slot = None
        else:
            end = (line, len(last_line.encode('utf-8')) + len(_CURSOR))
            slot = _ast_slot(tree, end)

        used_fallback = slot is None
        if used_fallback:
            slot = _Slot('neutral')
        visible = dict.fromkeys(word for word in reversed(names) if not keyword.iskeyword(word))
        recent_names = tuple(islice(visible, 64))
        ranked = {}
        for group in _candidate_groups(slot, recent_names):
            for word in sorted(group):
                if (word.startswith(partial) and word != partial and word not in ranked
                        and _fits_slot(slot.kind, word)):
                    ranked[word] = None
                    if len(ranked) == limit:
                        return Prediction(tuple(ranked), slot.kind, parser, used_fallback)
        return Prediction(tuple(ranked), slot.kind, parser, used_fallback)
