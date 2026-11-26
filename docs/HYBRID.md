# AST and n-gram hybrid (T12)

The hybrid wraps a fitted word or character n-gram. It uses the standalone AST predictor to rerank full-word suggestions. Both predictors receive the same text before the cursor. The hybrid needs no extra corpus fitting and uses the n-gram's training vocabulary.

## Run an example

Use Python 3.12 from the repository root.

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

```python
from hybrid_predictor import HybridPredictor
from ngram_models import WordNGramModel

ngram = WordNGramModel(n=2)
ngram.fit(['private = 1\nprint(private)\n'])
hybrid = HybridPredictor(ngram)
print(hybrid.suggest('call(pri'))
print(hybrid.predict('call(pri')))
```

In the project evaluator, pass the already fitted n-gram into `HybridPredictor`. A saved n-gram can also be loaded using the corresponding model class before constructing the hybrid.

## Ranking and fallback

1. Ask both models for up to `max(pool_size, limit)` suggestions. The default pool size is 25, which lets AST agreement promote a candidate outside the first five.
2. For each n-gram candidate, calculate `1 / ngram_rank`. If the same word is also among the AST suggestions, add `ast_weight / ast_rank`. Ranks start at 1 and `ast_weight` defaults to 0.75. Sort by descending total and break ties lexicographically. Return up to `limit` full words.
3. Keep the original n-gram order when the AST predictor cannot identify a context, has no candidates for that context, or has no candidates in common with the n-gram. Return an empty result immediately when the n-gram has no candidates.

The AST bonus is based on exact candidate agreement, so the two models' raw scores do not need to be comparable. An n-gram candidate can still appear without AST agreement. The hybrid relies on the n-gram for partial matching, lexical suppression, and candidate coverage. It cannot recover a word outside the n-gram candidate pool.

`predict(prefix, limit)` exposes `suggestions`, `context`, `parser`, `used_fallback`, and `fallback_reason`. Fallback reasons are `ast_context_unavailable`, `no_ast_candidates`, and `no_overlap`. Empty n-gram output has no fallback reason, since there is no pool to rerank or fall back to. `suggest(prefix, limit)` returns the shared list of words.

## Evaluation handoff

The default weight and pool size are starting values for development. Use the shared cases and evaluator from T10 as they become available. In each development fold, fit the n-gram only on that fold's training projects and compare the n-gram, standalone AST, and hybrid on the same validation cases. Log parser use, fallbacks, and empty suggestions separately. Use only development results to choose the n-gram and hybrid settings, then refit on all development projects before running the final held-out comparison. The n-gram selection comes from T11.
