# Project backlog

This is our working task list, not a list of extra course requirements. T01 and T03 are complete. The remaining task statuses are tracked in GitHub issues.

Workflow: **Todo -> In progress -> Review -> Done**. Pick one task at a time, make a branch named after its ID (for example `t06-word-model`), and link the pull request to the task. Move it to Done after the other person reviews it and its completion checks pass.

Each task has one accountable owner. David owns data, n-grams, the evaluator, n-gram experiments, report and submission. Kamso owns interfaces, parsing, AST, hybrid implementation and experiments, editor and demonstration. The other partner reviews relevant work and supplies needed inputs.

## Epics and user stories

- **Setup:** As teammates, we want a shared repo and agreed interfaces so we can work separately and combine our work.
- **Data:** As experimenters, we want documented, repeatable source data so comparisons use the same inputs.
- **Models:** As a coder, I want useful next-word suggestions so I spend less time typing repeated code.
- **Evaluation:** As experimenters, we want fair measurements so we can explain which model works best.
- **Editor:** As a coder, I want five selectable suggestions while typing so I can try the models in practice.
- **Delivery:** As a team, we want reproducible results and a clear demo so others can understand our work.

## Tasks

### T01 Set up the shared repository

- Status: Done
- Epic: Setup | Owner: David | Milestone: M1 | Priority: High
- Depends on: None
- Done when: Both partners can access the repo; planning files are committed; both understand the first tasks.
- GitHub issue: [#1](https://github.com/davidibie/cosc329-mini-copilot/issues/1)
- Five-day target: Day 1


### T02 Agree on roles and prediction format

- Status: Done
- Epic: Setup | Owner: Kamso | Milestone: M1 | Priority: High
- Depends on: None
- Done when: Confirm Python, ownership and full-word suggestion format; record decisions in INTERFACES.md.
- GitHub issue: [#2](https://github.com/davidibie/cosc329-mini-copilot/issues/2)
- Five-day target: Day 1


### T03 Clarify evaluation split

- Status: Done
- Epic: Setup | Owner: David | Milestone: M1 | Priority: High
- Depends on: None
- Done when: Ask how 70/30 and five-fold CV fit together; record instructor guidance before formal experiments.
- GitHub issue: [#3](https://github.com/davidibie/cosc329-mini-copilot/issues/3)
- Five-day target: Day 1


### T04 Choose and log dataset sources

- Status: Done
- Epic: Data | Owner: David | Milestone: M2 | Priority: High
- Depends on: T02
- Done when: Log at least 10 independent Python projects with URL, license, exact commit and included paths.
- GitHub issue: [#4](https://github.com/davidibie/cosc329-mini-copilot/issues/4)
- Five-day target: Day 1


### T05 Prepare repeatable dataset and splits

- Status: Done
- Epic: Data | Owner: David | Milestone: M2 | Priority: High
- Depends on: T03 T04
- Done when: Exclude generated/vendor code consistently; deduplicate; save project-level splits, seed and file hashes; keep raw code out of Git.
- GitHub issue: [#5](https://github.com/davidibie/cosc329-mini-copilot/issues/5)
- Five-day target: Day 1


### T06 Build word n-gram models

- Status: Done
- Epic: Models | Owner: David | Milestone: M2 | Priority: High
- Depends on: T02
- Done when: Support n=1..10, smoothing and unseen contexts; document tokenization; test on small known sequences.
- GitHub issue: [#6](https://github.com/davidibie/cosc329-mini-copilot/issues/6)
- Five-day target: Day 2


### T07 Build character n-gram models

- Status: Done
- Epic: Models | Owner: David | Milestone: M2 | Priority: High
- Depends on: T02
- Done when: Support n=1..10; generate full-word candidates with length/stop limits; expose the agreed suggestion interface.
- GitHub issue: [#7](https://github.com/davidibie/cosc329-mini-copilot/issues/7)
- Five-day target: Day 2


### T08 Try a parser on incomplete code

- Status: Done
- Epic: Models | Owner: Kamso | Milestone: M2 | Priority: High
- Depends on: T02
- Done when: Compare candidate parser behaviour on unfinished expressions; select an error-tolerant approach and document failure cases.
- GitHub issue: [#8](https://github.com/davidibie/cosc329-mini-copilot/issues/8)
- Five-day target: Day 1


### T09 Build the AST prediction baseline

- Status: Done
- Epic: Models | Owner: Kamso | Milestone: M3 | Priority: High
- Depends on: T08
- Done when: Produce ranked word candidates from prefix structure; document candidate rules, syntax checks and fallback; never use hidden future text.
- GitHub issue: [#9](https://github.com/davidibie/cosc329-mini-copilot/issues/9)
- Five-day target: Day 2


### T10 Build shared contexts and metrics

- Status: Review
- Epic: Evaluation | Owner: David | Milestone: M3 | Priority: High
- Depends on: T02
- Done when: Score the same held-out word targets for every model; verify exact-match accuracy and character edit distance with hand-worked cases.
- GitHub issue: [#10](https://github.com/davidibie/cosc329-mini-copilot/issues/10)
- Five-day target: Day 3


### T11 Run five-fold model comparisons

- Status: In progress
- Epic: Evaluation | Owner: David | Milestone: M3 | Priority: High
- Depends on: T05 T06 T07 T10
- Done when: Fit on each training fold only; save per-fold results for every n plus mean and sample SD; record runtime settings and failures.
- GitHub issue: [#11](https://github.com/davidibie/cosc329-mini-copilot/issues/11)
- Five-day target: Day 3


### T12 Evaluate AST and hybrid models

- Status: In progress
- Epic: Evaluation | Owner: Kamso | Milestone: M4 | Priority: High
- Depends on: T09 T10 T11
- Done when: Kamso implements syntax integration and the hybrid, runs AST and hybrid comparisons using David's evaluator and common contexts, and gives David saved results and commands for the report. Tune on development data, then compare the selected n-gram, AST and hybrid on the held-out set.
- GitHub issue: [#12](https://github.com/davidibie/cosc329-mini-copilot/issues/12)
- Five-day target: Day 3


### T13 Build a basic editor with fake predictions

- Status: Done
- Epic: Editor | Owner: Kamso | Milestone: M3 | Priority: High
- Depends on: T02
- Done when: Typing shows up to five suggestions; selecting one replaces the partial word; use a fake model first so work can start immediately.
- GitHub issue: [#13](https://github.com/davidibie/cosc329-mini-copilot/issues/13)
- Five-day target: Day 2


### T14 Connect two models and handle failures

- Status: Done
- Epic: Editor | Owner: Kamso | Milestone: M4 | Priority: High
- Depends on: T09 T12 T13
- Done when: Switch between two selected models; update suggestions as code changes; handle empty output/parser errors and check typing responsiveness.
- GitHub issue: [#14](https://github.com/davidibie/cosc329-mini-copilot/issues/14)
- Five-day target: Day 4


### T15 Choose models and compare coding experience

- Status: In progress
- Epic: Evaluation | Owner: Kamso | Milestone: M4 | Priority: High
- Depends on: T11 T12 T14
- Done when: Explain the choice using results; both try the same coding tasks with two models; record useful and bad suggestions and actual observations.
- GitHub issue: [#15](https://github.com/davidibie/cosc329-mini-copilot/issues/15)
- Five-day target: Day 4


### T16 Prepare presentation and demonstration

- Status: Todo
- Epic: Delivery | Owner: Kamso | Milestone: M5 | Priority: High
- Depends on: T15
- Done when: Show problem, methods, results and limitations; rehearse the demo; confirm duration/format on Canvas before recording.
- GitHub issue: [#16](https://github.com/davidibie/cosc329-mini-copilot/issues/16)
- Five-day target: Day 5


### T17 Finish report and reproduce results

- Status: Todo
- Epic: Delivery | Owner: David | Milestone: M6 | Priority: High
- Depends on: T15
- Done when: Explain data, splits, methods, hybrid and metrics; include real tables and limitations; another partner reproduces the key run from README.
- GitHub issue: [#17](https://github.com/davidibie/cosc329-mini-copilot/issues/17)
- Five-day target: Day 5


### T18 Review final submission and contributions

- Status: Todo
- Epic: Delivery | Owner: David | Milestone: M6 | Priority: High
- Depends on: T16 T17
- Done when: Check current Canvas deliverables; confirm teaching-team access; record actual contributions; one submits and the other verifies.
- GitHub issue: [#18](https://github.com/davidibie/cosc329-mini-copilot/issues/18)
- Five-day target: Day 5

