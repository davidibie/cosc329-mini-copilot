# Mini co-pilot work split and milestones

We're building the two-person mini co-pilot option for COSC 329. This plan gives each person a starting area and keeps the shared experiment work visible. The split is proposed; agree on it together before treating it as a commitment.

## Roles

**David - data and n-grams:** collect and document Python projects, prepare the dataset, implement word/character models and lead repeatable experiment runs. Start with T04 and T06.

**Kamso - syntax and editor:** investigate incomplete-code parsing, build the AST baseline and editor, and lead syntax integration in the hybrid. Start with T08 and T13 using a fake predictor.

**Both - evaluation and delivery:** agree on prediction inputs and scored targets, define metrics, build the hybrid, compare two models, review each other's work and prepare the report/demo. Shared work is split into a named lead before coding.

## Milestones

Dates are in 2026, Pacific time. Internal targets are our proposed schedule, not extra instructor deadlines. Canvas due dates below come from the course assignment list; check the corresponding assignment page for format requirements.

### M1 Repository ready

Team target: Oct 30. Repository link due Nov 1 at 11:59 p.m.

Done when: Repository and planning files are ready; agree on roles; submit an accessible repository URL.

### M2 Dataset and first models

Team target: Nov 8. Internal target.

Done when: 10+ sources logged; stable project splits; character and word models work.

### M3 Structure and experiments

Team target: Nov 15. Internal target.

Done when: AST baseline and five-fold runner work; failures and metrics recorded.

### M4 Hybrid and editor

Team target: Nov 22. Internal target.

Done when: Hybrid evaluated; editor shows five suggestions and can switch models.

### M5 Presentation ready

Team target: Nov 27. Presentation due Nov 29 at 11:59 p.m.

Done when: Compare two models; record demo; check the separate Canvas presentation instructions.

### M6 Final handoff

Team target: Dec 11. Final deliverables due Dec 13 at 11:59 p.m.

Done when: Reproduce results; finish report; check and submit the required final files.

## Settle these first

- Confirm Python as both the dataset language and implementation language.
- Agree on what counts as a word target and how partial-word completion works.
- Confirm how the general 70/30 split relates to the two-person five-fold requirement. Our proposal is a 30% project-level final holdout and five development folds within the remaining 70%; it needs instructor confirmation. Ten total projects would leave very small folds, so consider a larger dataset.
- Use only training-fold vocabulary and statistics when fitting a model. Every model receives the same prefix and hidden target boundary. Never give a predictor the rest of the file.

## Work independently

Before implementing models, agree on a shared prediction interface. One possible shape is `fit(source_strings)` and `suggest(prefix, limit=5)`, but this is a proposal, not existing code. David can work on tiny sample files while Kamso uses a fake predictor to build the editor. Document shared changes in INTERFACES.md before using them on both branches.

## What done means

Relevant tests pass, another partner has reviewed the work, and setup instructions match the code. Dataset choices and experiment settings are recorded. Results come from saved runs; example output is not evidence of model quality.

Keep one active task per person where possible. Use short updates: finished, next, blocked. The task IDs and acceptance checks live in BACKLOG.md.

## Scope

We need character and word n-grams for n=1..10, an AST model, a hybrid and a simple editor with five suggestions. Keep the editor basic. Chat, cloud model services, accounts and a full IDE extension are outside this plan.

Course guidance: https://cmps-people.ok.ubc.ca/bowenhui/analytics/project.html
