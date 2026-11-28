# Shared evaluation and n-gram selection

Run the benchmark from the repository root with Python 3.12 and the pinned corpus available locally.

```sh
python scripts/prepare_data.py
python -m unittest discover -s tests
python scripts/compare_ngrams.py --workers 5 --output results/ngram-cross-validation.json
```

The runner fits every word and character order from 1 through 10 at alpha 1.0. Each of the five folds fits on its training projects and scores the same cases from its validation projects. The six final test projects stay outside selection. The default uses every eligible target. A case ID consists of project, path, line and zero-based column. The run records the manifest hash and the digest of each ordered case list, so subsequent development runs can check that they used identical contexts.

Each case places the cursor before one eligible Python NAME as defined in [the prediction interface](INTERFACES.md). The predictor receives the left prefix. Top-one accuracy and mean character Levenshtein distance score the first suggestion. An empty suggestion counts as a miss and incurs the length of the expected word. Top-five accuracy, empty outputs, fallback reasons and prediction errors are logged separately. Fold means weight each fold equally, and standard deviations are sample standard deviations. Selection maximizes mean top-one accuracy, then minimizes mean edit distance, then favors smaller order and sorts by family for a deterministic last tie-break.

The n-gram comparison caches equivalent contexts and shares character transitions across candidate spellings. It preserves the live predictor rankings. Recorded evaluation times include the scoring and ranking but exclude shared case extraction and context preparation. Use measured editor response times for the practical comparison.

## Refit the selected n-gram

The [saved development run](../results/ngram-cross-validation.json) selected the word 10-gram at alpha 1.0. See the [development results](REPORT.md#n-gram-development-results) for the complete comparison table. Refit this configuration on all 14 development projects for the editor and for the locked final test.

```sh
python scripts/train_model.py --family word --n 10 --output models/editor-selected.json
python editor.py --family word --model models/editor-selected.json
```

The editor command uses the default hybrid settings. Supply the pool size and AST weight chosen in the development run before recording final observations.

## Use the same cases for the AST and hybrid

`scripts.compare_ngrams.load_cases(manifest_path, projects, raw)` yields the cases from the pinned source files in manifest order. Pass the same materialized list to `evaluation.evaluate(predictor, cases)` for every predictor in an experiment. The evaluator accepts `suggest(prefix, limit=5)` and also reads fallback diagnostics from the AST and hybrid `predict` methods. Fit the selected n-gram separately on each fold's training projects before tuning the hybrid with validation cases. After fixing settings, fit on all development projects, then use `test_projects` to compare the selected n-gram, AST and hybrid in one held-out run.

## Report notes

- Explain why entire projects are kept together and why the six test projects stay out of model selection.
- Compare the best order within each family, how much the scores vary by fold, and how the character model's scoring favors certain word lengths.
- Add the locked held-out comparison and both participants' actual editor observations once they are available. Keep the two forms of evidence distinct.
- Discuss the limits of predicting a whole word with an empty partial, project distribution and vocabulary coverage, and static rules for AST candidates.
