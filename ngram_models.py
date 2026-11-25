"""Word and character n-grams that rank full Python NAME completions."""

import json
import math
import os
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from text_processing import prediction_context, word_tokens

UNKNOWN = '\x01'
END_WORD = '\x00'


class NGramModel:
    """Common smoothed count tables and versioned JSON persistence."""

    def __init__(self, n=2, alpha=1.0):
        if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 10:
            raise ValueError('n must be an integer from 1 through 10')
        if not math.isfinite(alpha) or alpha <= 0:
            raise ValueError('alpha must be finite and positive')
        self.n = n
        self.alpha = float(alpha)
        self.vocabulary = set()
        self.symbols = set()
        self.counts = defaultdict(Counter)
        self.totals = Counter()

    def _observe(self, context, symbol):
        for length in range(min(self.n - 1, len(context)) + 1):
            key = tuple(context[-length:]) if length else ()
            self.counts[key][symbol] += 1
            self.totals[key] += 1

    def probability(self, symbol, context=()):
        """Add-alpha smoothing after backing off to the longest observed context."""
        key = tuple(context[-(self.n - 1):]) if self.n > 1 else ()
        while key and key not in self.counts:
            key = key[1:]
        if symbol not in self.symbols:
            symbol = UNKNOWN
        return (self.counts.get(key, {}).get(symbol, 0) + self.alpha) / (
            self.totals.get(key, 0) + self.alpha * (len(self.symbols) + 1))

    def suggest(self, prefix, limit=5):
        if limit <= 0:
            return []
        context = prediction_context(prefix)
        if context is None or not self.vocabulary:
            return []
        names, partial = context
        candidates = [word for word in self.vocabulary
                      if word.startswith(partial) and (not partial or len(word) > len(partial))]
        scores = self._scores(prefix, names, partial, candidates)
        return sorted(candidates, key=lambda word: (-scores[word], word))[:limit]

    def save(self, path):
        """Replace a model file atomically so a failed write cannot corrupt it."""
        payload = {'version': 1, 'model_type': type(self).__name__, 'n': self.n,
                   'alpha': self.alpha, 'vocabulary': sorted(self.vocabulary),
                   'symbols': sorted(self.symbols),
                   'counts': [[list(context), dict(sorted(counts.items()))]
                              for context, counts in sorted(self.counts.items())]}
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
            try:
                json.dump(payload, handle, ensure_ascii=False, separators=(',', ':'))
                handle.write('\n')
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        try:
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)

    @classmethod
    def load(cls, path):
        payload = json.loads(Path(path).read_text())
        if payload.get('version') != 1 or payload.get('model_type') != cls.__name__:
            raise ValueError('Unsupported model version or model type')
        model = cls(payload['n'], payload['alpha'])
        model.vocabulary = set(payload['vocabulary'])
        model.symbols = set(payload['symbols'])
        for context, counts in payload['counts']:
            key = tuple(context)
            if len(key) >= model.n or any(not isinstance(value, int) or value <= 0 for value in counts.values()):
                raise ValueError('Invalid saved count table')
            model.counts[key] = Counter(counts)
            model.totals[key] = sum(counts.values())
        return model

    def _reset(self):
        self.vocabulary.clear()
        self.symbols.clear()
        self.counts.clear()
        self.totals.clear()


class WordNGramModel(NGramModel):
    """n includes the next NAME and at most n-1 preceding NAME tokens."""

    def fit(self, source_strings):
        self._reset()
        for source in source_strings:
            previous = []
            for item in word_tokens(source):
                word = item.string
                self.vocabulary.add(word)
                self.symbols.add(word)
                self._observe(previous, word)
                previous.append(word)
                if len(previous) > self.n - 1:
                    previous.pop(0)

    def _scores(self, prefix, names, partial, candidates):
        return {word: self.probability(word, names) for word in candidates}


class CharacterNGramModel(NGramModel):
    """Score complete words using character transitions and an end-word marker."""

    def fit(self, source_strings):
        self._reset()
        for source in source_strings:
            lines = source.splitlines(keepends=True)
            offsets = [0]
            for line in lines:
                offsets.append(offsets[-1] + len(line))
            for item in word_tokens(source):
                word = item.string
                self.vocabulary.add(word)
                position = offsets[item.start[0] - 1] + item.start[1]
                context = source[max(0, position - self.n + 1):position]
                for symbol in word + END_WORD:
                    self.symbols.add(symbol)
                    self._observe(context, symbol)
                    context = (context + symbol)[-(self.n - 1):] if self.n > 1 else ''

    def _scores(self, prefix, names, partial, candidates):
        scores = {}
        # Include the visible partial in the character context, scoring only its completion.
        context = prefix[-(self.n - 1):] if self.n > 1 else ''
        for word in candidates:
            history = context
            suffix = word[len(partial):] + END_WORD
            score = 0.0
            for symbol in suffix:
                score += math.log(self.probability(symbol, history))
                history = (history + symbol)[-(self.n - 1):] if self.n > 1 else ''
            scores[word] = score / len(suffix)
        return scores
