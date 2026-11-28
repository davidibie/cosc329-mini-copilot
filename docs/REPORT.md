# Mini Copilot technical report

Working draft. The development benchmark, final held-out comparison and paired editor exercise supply separate evidence for this report.

## Goal

Mini Copilot suggests up to five Python words immediately before the cursor. We compare models that learn from previous tokens or characters with a rules-based structure predictor, then test whether the AST model improves the best n-gram when it reranks the n-gram's candidates.

## Dataset and split

We pinned 20 Python libraries, with URLs, commits and licenses recorded in [the source list](../data/sources.csv). The [manifest](../data/manifest.json) selects 204 files and records hashes and counts. The preparation script excludes tests, examples and generated files, caps the file size and number of files per project, and removes exact and normalized-token duplicates. Python 3.12 tokenization defines a word as a NAME token, including identifiers and keywords. It excludes comments, literals and f-string interpolations from targets.

| Partition | Projects | Files | Eligible words |
| --- | ---: | ---: | ---: |
| Development | 14 | 148 | 85,733 |
| Final test | 6 | 56 | 33,417 |

The development set is split into five folds. Every validation project stays entirely outside its fold's training set, including when building the vocabulary. The five validation sets contain 17,975, 11,453, 18,193, 19,282 and 18,830 target words. We keep the final test projects separate until the n-gram and hybrid settings are fixed. Grouping by project tests transfer to codebases new to the model and reduces the risk of closely related files appearing across a split.

## Models

- The word n-gram counts successive Python NAME tokens within a file and ranks training-vocabulary candidates by smoothed next-token probability. The character n-gram uses recent raw characters, predicts the remaining letters and an end-of-word marker, and ranks full candidates by mean log probability across those transitions. Both try orders 1 through 10 and use add-one smoothing and context backoff.
- The standalone AST model replaces a partial identifier with a synthetic cursor marker and tries to infer its syntactic role from the visible prefix. It uses Python's AST parser when the probe parses, with Parso recovery for unfinished code. Candidate groups depend on the slot and include visible names and a small inventory of common words. A neutral fallback covers unrecognized contexts.
- The hybrid obtains an n-gram pool of candidates and boosts words that the AST model also ranks. The score combines reciprocal n-gram rank with weighted reciprocal AST rank. A pool with no structural overlap retains its original order. The approach can promote an existing candidate, and its coverage depends on the n-gram pool.

## Evaluation

Each case hides a complete word and passes only the text before it. Top-one exact-match accuracy measures the fraction of targets predicted first. Mean character Levenshtein distance shows how many single-character edits would turn the first suggestion into the target. Empty output scores as a miss and uses the expected word's length for edit distance. We also report top-five accuracy because the editor displays five candidates. See [the benchmark commands and settings](EVALUATION.md).

The editor exercise uses four shared scenarios, including incomplete syntax, member completion, whole-identifier replacement and comment suppression. Both participants try each model in opposite orders and record suggestions, response times and what they preferred. The [exercise notes](EDITOR_COMPARISON.md) describe the dry run and worksheet.

## Limitations

The corpus is sampled from Python libraries and excludes files outside the pinned size and package filters. Some real editor inputs contain errors or partial words and differ from the benchmark's full-word cases. The training vocabulary misses new identifiers, and the AST predictor uses a limited set of candidate rules. Report fold variability alongside averages because validation projects differ in style and size. The two-person editor exercise describes the tested workflows and participants' observations.
