# Character and word predictors (T06–T07)

Both families support n=1 through n=10 through the same API. Use Python 3.12. Model code uses the standard library. `text_processing.word_tokens` provides shared NAME targets and excludes comments, literal strings and the entire contents of f-strings, including interpolations. The evaluator can reuse TokenInfo positions to construct targets later.

## Train and use

Prepare the corpus first as described in DATASET.md. From the repository root run the following commands.

```sh
python scripts/train_model.py --family word --n 3 --fold 1 --output models/word-3-fold1.json --prefix 'import '
python scripts/train_model.py --family character --n 3 --fold 1 --output models/character-3-fold1.json --prefix 'pri'
python -m unittest discover -s tests -v
```

Use `--fold 1` through `--fold 5` to fit only that fold's training projects. Omitting `--fold` fits on all 14 development projects; it never adds final-test projects. That full-development fit is for a final model once configuration choices are fixed, or for implementation smoke checks. The command prints the exact training projects and verifies predictions match after save/load. `n=3` in these examples is an illustration, not a selected best model. Formal comparison and selection are T11.

```python
from ngram_models import WordNGramModel, CharacterNGramModel

model = WordNGramModel(n=2, alpha=1.0)
model.fit(['print(value)\nprint(other)\n'])
model.suggest('pri', limit=5)
model.save('models/example.json')
restored = WordNGramModel.load('models/example.json')
```

Each fit replaces prior fitted state. Save files contain a format version, model type, n, alpha, training vocabulary, alphabet and count tables. They are JSON and remain under the ignored `models/` directory. A model of the wrong type or version is rejected on loading.

## Word model

An order n predicts the next NAME using up to n−1 preceding NAMEs. Other token types are omitted from this family's context. Keep case and original spelling. Each source file begins a new context. Count shorter contexts during training so an unseen longer context can back off to the longest observed suffix, ultimately unigram counts.

Use add-alpha smoothing with default alpha=1. For count c of a word after a context, total observations C, and V observed word types, probability is (c + alpha) / (C + alpha × (V + 1)). The additional category is an unknown word. It has positive probability but is not returned as a literal completion. Candidate suggestions come from the training vocabulary; unseen identifiers therefore remain a limitation.

## Character model

Extract the same eligible NAME targets. For each target, take up to n−1 characters of actual source immediately before it, then count character transitions through the word and an explicit end-word marker. The preceding characters may include whitespace and syntax. Context never crosses a file boundary.

For a typed prefix, start from its last n−1 characters and score each eligible candidate's remaining suffix followed by the end-word marker. Back off unseen contexts just as in the word family, and smooth across the learned character alphabet plus an unknown-character category. Average log transition probability across the suffix and end marker to avoid automatically preferring short words simply because fewer probabilities are multiplied. This is a documented ranking choice; the length-normalized score is not a normalized probability distribution over whole words.

Rank only complete words observed in training. The character family scores their spellings character by character rather than emitting a single character. Candidate length is therefore bounded by the longest observed training word, and scoring always stops at its end marker. This finite-vocabulary method cannot invent a new identifier. Case-sensitive partial matching and lexical suppression follow INTERFACES.md.

## Common behavior and checks

Return distinct words, best first, with lexical ordering for score ties. Return fewer than five if necessary, and none for an empty vocabulary, impossible partial, nonpositive limit, comment/string context or a directly adjacent numeric token. A partial word must be extended; a suggestion identical to an existing partial is excluded. Only prefix text reaches the predictor. Word boundaries and editor replacement remain separate responsibilities.

Tests cover all twenty family/order combinations, hand-calculated smoothing and character scores, unseen contexts, refitting, file boundaries, string/f-string suppression, Unicode identifiers, tie order, invalid configurations and save/load equivalence. Full-corpus fit/save/load checks are implementation validation; they do not replace five-fold accuracy/edit-distance experiments.
