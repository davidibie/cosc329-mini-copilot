"""Shared Python NAME targets and conservative cursor context (Python 3.12)."""

import io
import token
import tokenize


def is_identifier_character(character):
    return bool(character) and ('a' + character).isidentifier()


def identifier_suffix(prefix):
    start = len(prefix)
    while start and is_identifier_character(prefix[start - 1]):
        start -= 1
    return prefix[start:]


def word_tokens(source):
    """Yield TokenInfo NAME targets, excluding all f-string interpolation names."""
    depth = 0
    for item in tokenize.generate_tokens(io.StringIO(source).readline):
        kind = token.tok_name[item.type]
        if kind in {'FSTRING_START', 'TSTRING_START'}:
            depth += 1
        elif kind in {'FSTRING_END', 'TSTRING_END'}:
            depth -= 1
        elif item.type == tokenize.NAME and not depth:
            yield item


def prediction_context(prefix):
    """Return completed NAMEs and a partial, or None inside unsafe lexical input."""
    partial = identifier_suffix(prefix)
    if partial and not partial.isidentifier():
        return None
    line = prefix.count('\n') + 1
    column = len(prefix.rpartition('\n')[2])
    cursor = (line, column)
    start = (line, column - len(partial))
    names = []
    depth = 0
    try:
        for item in tokenize.generate_tokens(io.StringIO(prefix).readline):
            kind = token.tok_name[item.type]
            if kind in {'FSTRING_START', 'TSTRING_START'}:
                depth += 1
            elif kind in {'FSTRING_END', 'TSTRING_END'}:
                depth -= 1
            elif item.type == tokenize.COMMENT and item.end == cursor:
                return None
            elif item.type == tokenize.NUMBER and item.end == start:
                return None
            elif item.type == tokenize.ERRORTOKEN:
                return None
            elif item.type == tokenize.NAME and not depth:
                if not (partial and item.end == cursor):
                    names.append(item.string)
    except IndentationError:
        return None
    except tokenize.TokenError as error:
        if error.args[0] not in {'EOF in multi-line statement', 'unexpected EOF in multi-line statement'}:
            return None
    return None if depth else (names, partial)


def partial_word(prefix):
    """Editor-compatible view of the same lexical guard used by trained models."""
    context = prediction_context(prefix)
    return None if context is None else context[1]
