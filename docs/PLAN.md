# Mini co-pilot work split and milestones

We're building the two-person mini co-pilot option for COSC 329. This plan gives each person a starting area and keeps the shared experiment work visible. Task ownership below reflects the five-day split requested by David on November 24, 2026.

## Roles

**David (@davidibie)** owns T01, T03, T04, T05, T06, T07, T10, T11, T17 and T18. T01 is complete. David provides the dataset, splits, n-grams, common evaluator and n-gram comparisons, then assembles the report and checks submission.

**Kamso (@xokado)** owns T02, T08, T09, T12, T13, T14, T15 and T16. Kamso documents the agreed interface, builds parsing and AST prediction, implements and evaluates the hybrid using David's evaluator, builds the editor, organizes the experience comparison and prepares the demonstration.

Each issue has one accountable owner. Both partners still review relevant work, agree on the interface, try the editor and contribute their explanations to the report and demo.

## Five-day working plan

These are internal working-day targets. Verify current Canvas deadlines separately.

| Day | David | Kamso |
| --- | --- | --- |
| 1 | Record T03, choose sources T04, prepare data and splits T05 | Agree and document interface T02, investigate parser T08, start editor T13 |
| 2 | Build word and character n-grams T06–T07 | Build AST predictor T09 and finish fake-prediction editor T13 |
| 3 | Build common evaluator T10, run n-gram comparisons T11 | Develop hybrid and evaluate AST/hybrid T12 using David's evaluator |
| 4 | Assemble report and reproducible commands T17 | Finish held-out comparisons T12, connect editor models T14, organize experience comparison T15 |
| 5 | Finish report T17 and check submission T18 | Finish fixes, prepare and record demonstration T16 |

David should hand over a working n-gram and evaluator early on Day 3. Kamso can develop hybrid integration before the final n-gram selection is available, then substitute the selected model. Kamso provides saved results, commands, methods and editor observations for David's report. Start report notes on Day 1.

## Evaluation decision (T03)

Professor Hui replied on November 16 that the proposed setup generally seems reasonable depending on project size. She emphasized explaining development decisions, interpreting results and identifying possible improvements.

We choose a roughly 70/30 split by whole Python projects, with five-fold cross-validation within the 70% development portion. Use development results for model selection and hybrid tuning. Once choices are fixed, fit trainable components on the full development set and compare the selected n-gram, AST and hybrid on identical held-out cases from the 30%. Save split manifests and record project and token counts. Keep vocabulary and learned statistics restricted to each training split.

T03 can be completed once this decision and instructor guidance are recorded, as above.

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
- Record dataset size and fold sizes. Ten total projects leave small development folds, so consider a larger dataset.
- Use only training-fold vocabulary and statistics when fitting a model. Every model receives the same prefix and hidden target boundary. Never give a predictor the rest of the file.

## Work independently

Before implementing models, agree on a shared prediction interface. One possible shape is `fit(source_strings)` and `suggest(prefix, limit=5)`, but this is a proposal, not existing code. David can work on tiny sample files while Kamso uses a fake predictor to build the editor. Document shared changes in INTERFACES.md before using them on both branches.

## What done means

Relevant tests pass, another partner has reviewed the work, and setup instructions match the code. Dataset choices and experiment settings are recorded. Results come from saved runs; example output is not evidence of model quality.

Keep one active task per person where possible. Use short updates: finished, next, blocked. The task IDs and acceptance checks live in BACKLOG.md.

## Scope

We need character and word n-grams for n=1..10, an AST model, a hybrid and a simple editor with five suggestions. Keep the editor basic. Chat, cloud model services, accounts and a full IDE extension are outside this plan.

Course guidance: https://cmps-people.ok.ubc.ca/bowenhui/analytics/project.html
