# Decisions before we start coding

Nothing in this file is implemented yet. These are questions and proposed boundaries for David and Kamso to settle together.

## Predictions

- What should count as a word: identifiers, keywords, numbers, punctuation or some subset?
- How do we represent code before the cursor and a partly typed word?
- What should every model return so the editor can show the same five-suggestion list?
- One possible interface is `fit(source_strings)` and `suggest(prefix, limit=5)`. Decide before using it across both branches.

## Fair comparison

Use the same held-out word boundaries for every model. Predictors receive only the code before the cursor; the hidden next word and later source belong in the evaluator only. Agree on what to do when a parser fails or a model returns no suggestion.

## Data and results

Record source URLs, exact versions, licenses and exclusions in the dataset log. Agree on project-level data splits and remove duplicates across splits. Build vocabulary and fit counts on training data only. Save scores per fold before calculating averages and standard deviations.

## Suggested file ownership

David: future dataset and character/word model files.

Kamso: future parser, AST model and editor files.

Shared: evaluation, hybrid, dependency changes and report. Agree on a lead for each shared task before coding.

These files will be created when we start the matching backlog tasks. The editor can use temporary fixed suggestions while the models are being built, so neither person has to wait for the other.
