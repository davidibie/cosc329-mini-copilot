"""Common whole-word completion cases and metrics."""

import io
from collections import Counter
from dataclasses import dataclass
from time import perf_counter

from text_processing import word_tokens


@dataclass(frozen=True)
class Case:
    id: str
    source: str
    offset: int
    target: str

    @property
    def prefix(self):
        return self.source[:self.offset]


def word_cases(source, file_id):
    offsets = [0]
    for line in io.StringIO(source):
        offsets.append(offsets[-1] + len(line))
    for item in word_tokens(source):
        line, column = item.start
        yield Case(f'{file_id}:{line}:{column}', source, offsets[line - 1] + column, item.string)


def edit_distance(left, right):
    """Character Levenshtein distance with unit insertion, deletion and substitution."""
    previous = range(len(right) + 1)
    for row, a in enumerate(left, 1):
        current = [row]
        for column, b in enumerate(right, 1):
            current.append(min(previous[column] + 1, current[-1] + 1,
                               previous[column - 1] + (a != b)))
        previous = current
    return previous[-1]


def evaluate(predictor, cases, *, suggest_case=None):
    """Score identical cases and record empty outputs, fallbacks and failures."""
    count = exact = top_five = edits = empty = 0
    failures = Counter()
    fallbacks = Counter()
    start = perf_counter()
    for case in cases:
        count += 1
        try:
            if suggest_case is not None:
                suggestions = suggest_case(case)
            elif hasattr(predictor, 'predict'):
                result = predictor.predict(case.prefix, limit=5)
                suggestions = result.suggestions
                if result.used_fallback:
                    fallbacks[getattr(result, 'fallback_reason', None) or result.context] += 1
            else:
                suggestions = predictor.suggest(case.prefix, limit=5)
        except Exception as error:
            failures[type(error).__name__] += 1
            suggestions = ()
        first = suggestions[0] if suggestions else ''
        exact += first == case.target
        top_five += case.target in suggestions
        empty += not suggestions
        edits += edit_distance(first, case.target)
    if not count:
        raise ValueError('No evaluation cases')
    return {'cases': count, 'top1_accuracy': exact / count, 'top5_accuracy': top_five / count,
            'mean_edit_distance': edits / count, 'empty_outputs': empty, 'failures': dict(failures),
            'fallbacks': dict(fallbacks), 'evaluation_seconds': perf_counter() - start}
