"""Rerank n-gram candidates using the standalone AST predictor."""

from dataclasses import dataclass
from math import isfinite

from ast_predictor import ASTPredictor


@dataclass(frozen=True)
class HybridPrediction:
    suggestions: tuple[str, ...]
    context: str | None = None
    parser: str | None = None
    fallback_reason: str | None = None

    @property
    def used_fallback(self) -> bool:
        return self.fallback_reason is not None


class HybridPredictor:
    """Use AST agreement to boost candidates already proposed by a fitted n-gram."""

    def __init__(self, ngram, *, pool_size: int = 25, ast_weight: float = 0.75):
        if isinstance(pool_size, bool) or not isinstance(pool_size, int) or pool_size < 1:
            raise ValueError('pool_size must be a positive integer')
        if not isfinite(ast_weight) or ast_weight < 0:
            raise ValueError('ast_weight must be finite and nonnegative')
        self.ngram = ngram
        self.pool_size = pool_size
        self.ast_weight = ast_weight
        self._ast = ASTPredictor()

    def suggest(self, prefix: str, limit: int = 5) -> list[str]:
        return list(self.predict(prefix, limit).suggestions)

    def predict(self, prefix: str, limit: int = 5) -> HybridPrediction:
        """Return reranked suggestions and the reason for any n-gram fallback."""
        if limit <= 0:
            return HybridPrediction(())

        pool_limit = max(self.pool_size, limit)
        candidates = self.ngram.suggest(prefix, pool_limit)
        if not candidates:
            return HybridPrediction(())

        syntax = self._ast.predict(prefix, pool_limit)
        ngram_order = tuple(candidates[:limit])
        if syntax.used_fallback:
            return HybridPrediction(ngram_order, syntax.context, syntax.parser, 'ast_context_unavailable')
        if not syntax.suggestions:
            return HybridPrediction(ngram_order, syntax.context, syntax.parser, 'no_ast_candidates')

        ast_ranks = {word: rank for rank, word in enumerate(syntax.suggestions, 1)}
        if ast_ranks.keys().isdisjoint(candidates):
            return HybridPrediction(ngram_order, syntax.context, syntax.parser, 'no_overlap')

        scores = []
        for rank, word in enumerate(candidates, 1):
            ast_rank = ast_ranks.get(word)
            bonus = self.ast_weight / ast_rank if ast_rank is not None else 0.0
            scores.append((word, 1 / rank + bonus))
        scores.sort(key=lambda entry: (-entry[1], entry[0]))
        suggestions = tuple(word for word, _ in scores[:limit])
        return HybridPrediction(suggestions, syntax.context, syntax.parser)
