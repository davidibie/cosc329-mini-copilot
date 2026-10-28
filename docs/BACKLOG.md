# Project backlog

This is our working task list, not a list of extra course requirements. All tasks below are still Todo. No models, tests or demo code have been implemented in this starter.

Workflow: **Todo -> In progress -> Review -> Done**. Pick one task at a time, make a branch named after its ID (for example `t06-word-model`), and link the pull request to the task. Move it to Done after the other person reviews it and its completion checks pass.

David owns the data and n-gram track, Kamso owns the parser and editor track, and Both means one leads the implementation while the other reviews it. Agree on the lead before starting shared tasks.

## Epics and user stories

- **Setup:** As teammates, we want a shared repo and agreed interfaces so we can work separately and combine our work.
- **Data:** As experimenters, we want documented, repeatable source data so comparisons use the same inputs.
- **Models:** As a coder, I want useful next-word suggestions so I spend less time typing repeated code.
- **Evaluation:** As experimenters, we want fair measurements so we can explain which model works best.
- **Editor:** As a coder, I want five selectable suggestions while typing so I can try the models in practice.
- **Delivery:** As a team, we want reproducible results and a clear demo so others can understand our work.

## Tasks

### T01 Set up the shared repository

- Status: Todo
- Epic: Setup | Owner: David | Milestone: M1 | Priority: High
- Depends on: None
- Done when: Both partners can access the repo; planning files are committed; both understand the first tasks.

### T02 Agree on roles and prediction format

- Status: Todo
- Epic: Setup | Owner: Both | Milestone: M1 | Priority: High
- Depends on: None
- Done when: Confirm Python, ownership and full-word suggestion format; record decisions in INTERFACES.md.

### T03 Clarify evaluation split

- Status: Todo
- Epic: Setup | Owner: David | Milestone: M1 | Priority: High
- Depends on: None
- Done when: Ask how 70/30 and five-fold CV fit together; record instructor guidance before formal experiments.

### T04 Choose and log dataset sources

- Status: Todo
- Epic: Data | Owner: David | Milestone: M2 | Priority: High
- Depends on: T02
- Done when: Log at least 10 independent Python projects with URL, license, exact commit and included paths.

### T05 Prepare repeatable dataset and splits

- Status: Todo
- Epic: Data | Owner: David | Milestone: M2 | Priority: High
- Depends on: T03 T04
- Done when: Exclude generated/vendor code consistently; deduplicate; save project-level splits, seed and file hashes; keep raw code out of Git.

### T06 Build word n-gram models

- Status: Todo
- Epic: Models | Owner: David | Milestone: M2 | Priority: High
- Depends on: T02
- Done when: Support n=1..10, smoothing and unseen contexts; document tokenization; test on small known sequences.

### T07 Build character n-gram models

- Status: Todo
- Epic: Models | Owner: David | Milestone: M2 | Priority: High
- Depends on: T02
- Done when: Support n=1..10; generate full-word candidates with length/stop limits; expose the agreed suggestion interface.

### T08 Try a parser on incomplete code

- Status: Todo
- Epic: Models | Owner: Kamso | Milestone: M2 | Priority: High
- Depends on: T02
- Done when: Compare candidate parser behaviour on unfinished expressions; select an error-tolerant approach and document failure cases.

### T09 Build the AST prediction baseline

- Status: Todo
- Epic: Models | Owner: Kamso | Milestone: M3 | Priority: High
- Depends on: T08
- Done when: Produce ranked word candidates from prefix structure; document candidate rules, syntax checks and fallback; never use hidden future text.

### T10 Build shared contexts and metrics

- Status: Todo
- Epic: Evaluation | Owner: Both | Milestone: M3 | Priority: High
- Depends on: T02
- Done when: Score the same held-out word targets for every model; verify exact-match accuracy and character edit distance with hand-worked cases.

### T11 Run five-fold model comparisons

- Status: Todo
- Epic: Evaluation | Owner: David | Milestone: M3 | Priority: High
- Depends on: T05 T06 T07 T10
- Done when: Fit on each training fold only; save per-fold results for every n plus mean and sample SD; record runtime settings and failures.

### T12 Evaluate AST and hybrid models

- Status: Todo
- Epic: Evaluation | Owner: Both | Milestone: M4 | Priority: High
- Depends on: T09 T10 T11
- Done when: Kamso leads syntax integration; David leads experiment runs; compare AST and a documented hybrid with n-gram baselines using the same contexts.

### T13 Build a basic editor with fake predictions

- Status: Todo
- Epic: Editor | Owner: Kamso | Milestone: M3 | Priority: High
- Depends on: T02
- Done when: Typing shows up to five suggestions; selecting one replaces the partial word; use a fake model first so work can start immediately.

### T14 Connect two models and handle failures

- Status: Todo
- Epic: Editor | Owner: Kamso | Milestone: M4 | Priority: High
- Depends on: T09 T12 T13
- Done when: Switch between two selected models; update suggestions as code changes; handle empty output/parser errors and check typing responsiveness.

### T15 Choose models and compare coding experience

- Status: Todo
- Epic: Evaluation | Owner: Both | Milestone: M4 | Priority: High
- Depends on: T11 T12 T14
- Done when: Explain the choice using results; both try the same coding tasks with two models; record useful and bad suggestions and actual observations.

### T16 Prepare presentation and demonstration

- Status: Todo
- Epic: Delivery | Owner: Both | Milestone: M5 | Priority: High
- Depends on: T15
- Done when: Show problem, methods, results and limitations; rehearse the demo; confirm duration/format on Canvas before recording.

### T17 Finish report and reproduce results

- Status: Todo
- Epic: Delivery | Owner: Both | Milestone: M6 | Priority: High
- Depends on: T15
- Done when: Explain data, splits, methods, hybrid and metrics; include real tables and limitations; another partner reproduces the key run from README.

### T18 Review final submission and contributions

- Status: Todo
- Epic: Delivery | Owner: Both | Milestone: M6 | Priority: High
- Depends on: T16 T17
- Done when: Check current Canvas deliverables; confirm teaching-team access; record actual contributions; one submits and the other verifies.

