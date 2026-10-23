# Plan: <feature name>

Spec: `spec.md` · Status: DRAFT | APPROVED (<date>)

## Tasks

### TASK-1 <short title>
- Service: <name>
- Files: `path/a.py` (new), `path/b.py` (edit)
- Covers: REQ-1, EC-2
- Pattern: P-2 (`reference/file.py`)  <!-- or: NEW, because <reason> -->
- Reuses: `path/existing.py:function` <!-- existing code this task calls instead of writing it again, or "nothing" -->
- Steps: <2–5 bullets, concrete>
- Verify: `<command from CLAUDE.md>`

### TASK-2 ...

## Key details
<!-- Only for the key parts: new models and their fields, API contracts, shared components or helpers, and anything risky. Not every function. -->
### <key part, e.g. "Site model">
- How it will be built: <classes or functions with their signatures, fields with types, where each piece lives>
- Sketch, when the shape isn't obvious:
  ```python
  <short sketch of the non-obvious part>
  ```

## Order & dependencies
TASK-1 → TASK-2 → …
