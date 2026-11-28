# Editor comparison exercise (T15)

Kamso and David each complete the same tasks in the n-gram and hybrid modes. Both modes use the same fitted n-gram, so their comparison shows what changes when AST context reranks the suggestions.

## Choose and record the setup

Use the n-gram selected in T11 and the hybrid settings selected on development data in T12. Record the result links, the model file, model family, order and smoothing, and the hybrid pool size and AST weight. Both participants should use the same model configuration and perform both passes on the same device. See [editor setup](../README.md#try-the-editor) for training and launch commands.

The fold-1 word 3-gram and default hybrid settings in the README work for a practice run. Record final observations once the selected model and settings are available.

## Run both passes

Kamso starts with the n-gram and David starts with the hybrid. Start each task in a fresh buffer. Enter the starting text exactly as shown, using `|` as the cursor position. Wait for the suggestions to settle and record the visible order or target rank. Use the suggestion if it is present and finish by typing if it is missing. Record the outcome before switching models.

### 1. Complete an unfinished call

```python
call(pri|
```

Complete `print` and add the closing `)`. Note where `print` appears and record any distracting alternatives.

### 2. Complete a list method

```python
items = []
items.ap|
```

Complete `append` and add `(3)`. Check whether the editor suggests the method and preserves the receiver and dot.

### 3. Replace part of an existing identifier

```python
from pathlib import Pa|thBuilder
```

Choose `Path` if it appears. Check that the line becomes `from pathlib import Path` and that the caret lands after `Path`.

### 4. Check the comment behavior

```python
# pri|
```

Check whether the suggestion area clears and the editor remains responsive while typing or moving the cursor.

## Record observations

Each participant fills in their own copy of this table before discussing the results. For approximate responsiveness, record `<0.5 s`, `0.5–1 s`, or `>1 s` from the last edit or cursor move until the list settles. Record any pause in typing independently of the time the suggestions take to appear.

- Participant, date, platform and Python version
- Model file, launch command, model order and evaluation links

| Task | Mode | Target rank or missing | Helpful or distracting suggestions | Time | Acceptance, replacement or typing behavior |
| --- | --- | --- | --- | --- | --- |
| Open call | N-gram | | | | |
| Open call | Hybrid | | | | |
| List method | N-gram | | | | |
| List method | Hybrid | | | | |
| Mid-word import | N-gram | | | | |
| Mid-word import | Hybrid | | | | |
| Comment | N-gram | | | | |
| Comment | Hybrid | | | | |

After both passes, each person records their preferred mode, why, and one context that needs improvement. Give David both sets of observations for the report alongside the separate benchmark results.

## Automated dry run

The provisional fold-1 word 3-gram and its hybrid were exercised in the Tk editor. The hybrid moved `print` from fourth to second and surfaced `append` in second place where the n-gram's first five omitted it. Both modes suggested `Path` first, replaced the entire identifier, and cleared suggestions in the comment. The widget refreshed in about 84 to 109 ms on the test machine across these eight checks, including debounce and polling. These results verify the interaction paths. The participant rows are reserved for Kamso and David's own observations with the selected configuration.
