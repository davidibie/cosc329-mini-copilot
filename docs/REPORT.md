# Mini Copilot technical report

Working draft. The development benchmark, final held-out comparison and paired editor exercise supply separate evidence for this report.

## Goal

Mini Copilot suggests up to five Python words immediately before the cursor. We compare models that learn from previous tokens or characters with a rules-based structure predictor, then test whether the AST model improves the best n-gram when it reranks the n-gram's candidates.

## Dataset and split

We pinned 20 Python libraries, with URLs, commits and licenses recorded in [the source list](../data/sources.csv). The [manifest](../data/manifest.json) selects 204 files and records hashes and counts. The preparation script excludes tests, examples and generated files, caps the file size and number of files per project, and removes exact and normalized-token duplicates. Python 3.12 tokenization defines a word as a NAME token, including identifiers and keywords. It excludes comments, literals and f-string interpolations from targets.

| Partition | Projects | Files | NAME tokens before target filtering |
| --- | ---: | ---: | ---: |
| Development | 14 | 148 | 85,733 |
| Final test | 6 | 56 | 33,417 |

The development set is split into five folds. Every validation project stays entirely outside its fold's training set, including when building the vocabulary. The five validation sets contain 17,975, 11,453, 18,193, 19,282 and 18,830 NAME tokens before filtering f-string interpolations. The resulting validation case counts are 17,791, 11,257, 17,950, 18,981 and 18,351. We keep the final test projects separate until the n-gram and hybrid settings are fixed. Grouping by project tests transfer to codebases new to the model and reduces the risk of closely related files appearing across a split.

## Models

- The word n-gram counts successive Python NAME tokens within a file and ranks training-vocabulary candidates by smoothed next-token probability. The character n-gram uses recent raw characters, predicts the remaining letters and an end-of-word marker, and ranks full candidates by mean log probability across those transitions. Both try orders 1 through 10 and use add-one smoothing and context backoff.
- The standalone AST model replaces a partial identifier with a synthetic cursor marker and tries to infer its syntactic role from the visible prefix. It uses Python's AST parser when the probe parses, with Parso recovery for unfinished code. Candidate groups depend on the slot and include visible names and a small inventory of common words. A neutral fallback covers unrecognized contexts.
- The hybrid obtains an n-gram pool of candidates and boosts words that the AST model also ranks. The score combines reciprocal n-gram rank with weighted reciprocal AST rank. A pool with no structural overlap retains its original order. The approach can promote an existing candidate, and its coverage depends on the n-gram pool.

## Evaluation

Each case hides a complete word and passes only the text before it. Top-one exact-match accuracy measures the fraction of targets predicted first. Mean character Levenshtein distance shows how many single-character edits would turn the first suggestion into the target. Empty output scores as a miss and uses the expected word's length for edit distance. We also report top-five accuracy because the editor displays five candidates. See [the benchmark commands and settings](EVALUATION.md).

The editor exercise uses four shared scenarios, including incomplete syntax, member completion, whole-identifier replacement and comment suppression. Both participants try each model in opposite orders and record suggestions, response times and what they preferred. The [exercise notes](EDITOR_COMPARISON.md) describe the dry run and worksheet.

## N-gram development results

We scored all 20 configurations on 84,330 cases across five validation folds. Each metric below is the mean ± sample standard deviation across folds. Accuracy values are percentages with standard deviation in percentage points.

| Family | Order | Top-one accuracy (%) | Top-five accuracy (%) | Mean edit distance (characters) |
| --- | ---: | ---: | ---: | ---: |
| Word | 1 | 6.40 ± 1.06 | 18.56 ± 2.01 | 5.70 ± 0.36 |
| Word | 2 | 13.18 ± 2.10 | 27.48 ± 3.46 | 5.58 ± 0.39 |
| Word | 3 | 17.11 ± 4.01 | 29.31 ± 5.09 | 5.59 ± 0.41 |
| Word | 4 | 17.97 ± 5.02 | 28.73 ± 5.28 | 5.52 ± 0.46 |
| Word | 5 | 18.18 ± 5.35 | 28.63 ± 5.38 | 5.51 ± 0.47 |
| Word | 6 | 18.31 ± 5.55 | 28.62 ± 5.40 | 5.50 ± 0.49 |
| Word | 7 | 18.35 ± 5.60 | 28.60 ± 5.40 | 5.50 ± 0.49 |
| Word | 8 | 18.38 ± 5.63 | 28.60 ± 5.40 | 5.49 ± 0.49 |
| Word | 9 | 18.39 ± 5.64 | 28.60 ± 5.40 | 5.49 ± 0.49 |
| Word | 10 | 18.39 ± 5.64 | 28.60 ± 5.40 | 5.49 ± 0.49 |
| Character | 1 | 0.16 ± 0.13 | 1.73 ± 1.75 | 5.65 ± 0.40 |
| Character | 2 | 3.87 ± 0.47 | 15.50 ± 1.23 | 5.75 ± 0.35 |
| Character | 3 | 12.76 ± 2.05 | 24.46 ± 3.90 | 5.69 ± 0.37 |
| Character | 4 | 15.02 ± 2.06 | 25.27 ± 3.32 | 5.89 ± 0.35 |
| Character | 5 | 13.86 ± 1.94 | 24.14 ± 3.83 | 6.62 ± 0.40 |
| Character | 6 | 13.32 ± 2.76 | 22.19 ± 3.76 | 7.25 ± 0.45 |
| Character | 7 | 11.57 ± 1.96 | 21.16 ± 2.39 | 7.61 ± 0.44 |
| Character | 8 | 10.35 ± 1.89 | 19.14 ± 2.25 | 7.74 ± 0.40 |
| Character | 9 | 9.45 ± 1.57 | 17.30 ± 2.03 | 7.85 ± 0.34 |
| Character | 10 | 8.47 ± 1.65 | 15.92 ± 1.70 | 7.94 ± 0.35 |

The **word 10-gram** had the highest mean top-one accuracy (18.39%). Its fold accuracy ranged from 12.55% to 24.43%. The best character configuration by the same criterion was order 4 at 15.02%. The selected model produced at least one suggestion for 84,330 of 84,330 targets. See the [saved run](../results/ngram-cross-validation.json) for every fold's metrics, case counts, empty outputs and timings. These development results select the n-gram for hybrid tuning and the final held-out comparison.

## Limitations

The corpus is sampled from Python libraries and excludes files outside the pinned size and package filters. Some real editor inputs contain errors or partial words and differ from the benchmark's full-word cases. The training vocabulary misses new identifiers, and the AST predictor uses a limited set of candidate rules. Report fold variability alongside averages because validation projects differ in style and size. The two-person editor exercise describes the tested workflows and participants' observations.
