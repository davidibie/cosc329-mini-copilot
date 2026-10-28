# COSC 329 Mini Co-pilot

David and Kamso's two-person project for COSC 329.

We're planning a small tool that suggests what to type next while writing Python code. We'll compare models that learn patterns from existing code with an approach that uses the structure of the code, then try two models in a basic editor.

## Where we're at

This repo is our starting plan. There is no prediction code, dataset, editor or experiment output yet. Python is our proposed language; we'll confirm that together before collecting code.

## What's in the repo

- `docs/PLAN.md`: proposed roles, milestones and decisions to settle.
- `docs/BACKLOG.md`: tasks with owners, dependencies and checks for when each is done.
- `docs/backlog.json`: the same task list in a structured format.
- `docs/INTERFACES.md`: questions to agree on before connecting our code.
- `docs/Mini-Copilot-Work-Split.pdf`: shareable copy of the work split and milestones.
- `data/sources.csv`: blank table for recording the projects we use as data.

## What we need to build

- Collect code from at least 10 projects in one language and document the sources.
- Build character and word n-gram models for n = 1 through 10.
- Build a model using an abstract syntax tree, which represents code structure.
- Try combining our best n-gram model with the structure-based approach.
- Compare the models using accuracy and edit distance, including five-fold results with averages and standard deviations.
- Show five suggestions while typing in a basic editor, then compare the experience with two models.

The general project description mentions a 70/30 data split, while the two-person option asks for five-fold cross-validation. We'll clarify how these should fit together before running experiments.

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

Pick a task from the backlog, work on a separate branch and have the other person review the pull request. Keep the status and setup instructions current as we add code. There are no setup or run commands yet because implementation hasn't started.

Keep the raw dataset out of Git and record its source URLs, exact versions and licenses in `data/sources.csv`.

## Dates

Repository link: November 1, 2026 at 11:59 p.m. Pacific.

Presentation: November 29, 2026 at 11:59 p.m. Pacific.

Final deliverables: December 13, 2026 at 11:59 p.m. Pacific.

The plan includes earlier internal targets. Check Canvas for the current submission instructions.

Course guidance: https://cmps-people.ok.ubc.ca/bowenhui/analytics/project.html
