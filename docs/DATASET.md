# Dataset and split decisions (T04–T05)

We selected 20 independent Python libraries covering iterators, utilities, classes, web applications, HTTP, terminal output, dates, text formatting, templates, parsing and filesystem helpers. Several projects share the Pallets organization but are distinct repositories and libraries. The sample is library code, so our results will have limited generality to other Python domains.

`data/sources.csv` records repository URLs, exact commits, retrieval date, license, included package directories and selected file counts. License files were inspected in the pinned checkouts. Their paths and SHA256 hashes are in `data/manifest.json`; upstream sources retain the actual notices. Raw source is downloaded for local use and excluded from Git. Model redistributions may require retaining upstream notices and should be checked before publishing trained artifacts.

## Reproduce

Run with Python 3.12 and Git from the repository root.

```sh
python scripts/prepare_data.py
python scripts/prepare_data.py --offline
python -m unittest discover -s tests -v
```

The initial command fetches exact recorded commits. Existing tracked changes in a source checkout cause an error. Read files through `scripts.prepare_data.read_sources(manifest_path, projects)`, which verifies source hashes before yielding text. Never import or execute dataset source.

## Sampling and cleaning

- Inspect `.py` files only in the package directories listed in the source log.
- Exclude tests, docs, examples, vendor directories, symlinks and files with generated-code headers. Check Python 3.12 syntax and decoding; reject ineligible files with a recorded reason.
- Keep at most 12 files per project, each at most 49,152 bytes and containing at least 10 NAME tokens. Order candidates by SHA256 of `329:project:relative_path` so selection is repeatable and spreads across a package.
- Deduplicate across the entire selected corpus using raw byte hashes and normalized token-stream hashes. The latter ignores comments and whitespace. This catches exact copies and comment/formatting-only copies; it does not detect every near-duplicate or semantically equivalent implementation.
- Preserve original source text. Comments and strings are excluded from word targets by the shared tokenizer. Character contexts retain source spelling and spacing.
- Save every selected file's path, commit, SHA256, token hash, character count, byte count and NAME-token count. Save excluded paths and reasons too. Writes replace the manifest only after preparation succeeds.

The default preparation selected 204 files and 2,251,763 decoded characters. Sampling limits keep higher-order models manageable. The corpus is still small and identifiers may be unseen, so model smoothing and vocabulary limitations must be discussed in the report.

## Splits

Sort project names, shuffle with seed 329 and put the first floor(0.7 × project count) into development. With 20 projects, that gives 14 development and 6 final-test projects. Independently shuffle development project names with seed 330 and distribute them round-robin into five validation groups, of sizes 3, 3, 3, 3 and 2. Each fold trains on the other development projects. No project or selected file crosses a train/validation/test boundary.

The manifest contains `development_projects`, `test_projects` and each fold's `train_projects` and `validation_projects`. These refer to whole projects. File/token counts differ by group, so document those sizes with the results and interpret variability. All n values, both model families, AST and hybrid comparisons must reuse these assignments and the same prediction cases.

Use only training projects to derive vocabulary and counts in each fold. Choose n and hybrid settings from development results. After choices are fixed, fit on all development projects and evaluate once on the held-out final-test projects. Data preparation and file integrity checks can inspect test files; fitted statistics and model selection cannot use them.
