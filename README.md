# COSC 329 Mini Co-pilot

This a small tool that suggests what to type next while writing Python code. We'll compare models that learn patterns from existing code with an approach that uses the structure of the code, then try two models in a basic editor.

## Where we're at

Python is the implementation and dataset language. The editor prototype uses a fixed demo vocabulary while the trained models are being developed.

## Try the editor prototype

Run `python editor.py` from the repository root with Python 3.12 or later and Tkinter available. Type `pri`, then select `print`. To test replacement in the middle of an identifier, put the cursor after `pri` in `printrange` and select `print`. The whole identifier becomes `print`.

## What's in the repo

- `docs/PLAN.md`: proposed roles, milestones and decisions to settle.
- `docs/BACKLOG.md`: tasks with owners, dependencies and checks for when each is done.
- `docs/backlog.json`: the same task list in a structured format.
- `docs/INTERFACES.md`: the accepted predictor, token and metric contract.
- `docs/Mini-Copilot-Work-Split.pdf`: shareable copy of the work split and milestones.
- `data/sources.csv`: 20 pinned source projects, licenses and selected file counts.

## What we need to build

- Collect code from at least 10 projects in one language and document the sources.
- Build character and word n-gram models for n = 1 through 10.
- Build a model using an abstract syntax tree, which represents code structure.
- Try combining our best n-gram model with the structure-based approach.
- Compare the models using accuracy and edit distance, including five-fold results with averages and standard deviations.
- Show five suggestions while typing in a basic editor, then compare the experience with two models.

We use 70% of whole projects for development, run five-fold cross-validation within that portion, and reserve 30% for final testing. See docs/PLAN.md for the instructor guidance and decision.

## Proposed work split

David: dataset preparation and n-gram models.

Kamso: parser investigation, structure-based model and editor.

Both: evaluation, hybrid model, integration, report and demo. We can adjust the split after discussing it.

## First session

1. Read the course requirements together and agree on the work split.
2. Confirm Python and choose the first dataset sources.
3. Agree on the prediction input/output and what counts as a word.
4. Start the first small model ourselves and check its predictions by hand.

## How we'll work

Pick a task from the backlog, work on a separate branch and have the other person review the pull request. Keep the status and setup instructions current as we add code.

Keep the raw dataset out of Git and record its source URLs, exact versions and licenses in `data/sources.csv`.

## Dates

Repository link: November 1, 2026 at 11:59 p.m. Pacific.

Presentation: November 29, 2026 at 11:59 p.m. Pacific.

Final deliverables: December 13, 2026 at 11:59 p.m. Pacific.

The plan includes earlier internal targets. Check Canvas for the current submission instructions.

Course guidance: https://cmps-people.ok.ubc.ca/bowenhui/analytics/project.html

## Prepare the dataset

Use Python 3.12 and Git. The source projects are read as text, so their runtime dependencies are unnecessary.

```sh
python scripts/prepare_data.py
python -m unittest discover -s tests -v
```

The first command downloads exact commits into ignored `data/raw/` and writes `data/manifest.json`. Use `--offline` to rebuild from existing checkouts. See [dataset decisions](docs/DATASET.md) for sampling, exclusions, deduplication and fold usage.
