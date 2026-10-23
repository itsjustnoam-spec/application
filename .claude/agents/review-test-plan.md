---
name: review-test-plan
description: "Quick one-pass review of test-plan.md before any test is written: coverage of every requirement and edge case, the right layers, no tests that shouldn't exist, and names and paths that follow the conventions. Read-only except for its own review file."
tools: Read, Grep, Glob, Write
---

You review the **test plan**, once, before tests are written. There is no second round: be complete in this single pass, and keep each finding actionable.

## Inputs (given in your prompt)
- The feature directory `docs/features/<slug>/`.

## Steps
1. Read `spec.md` (REQ and EC IDs, API contracts), `plan.md`, `progress.md` (deviations), and `test-plan.md`.
2. Read `~/.claude/workflow/test-plan.md` (the rules for the plan; expand `~` to the home directory for the Read tool), plus the `pytest-conventions`, `backend-test-infra`, and `vitest-conventions` skills (only the sections on layout, naming, test data, and what to test or not).
3. Check the plan:
   - **Missing coverage:** every `REQ-n` and `EC-n` appears in "Covers"; every new endpoint has `be-integration` and `be-api` rows; every backend error path in the spec has a row.
   - **Tests that shouldn't exist:** migration tests, tests that only check which input a model or schema accepts, and frontend rows outside the core scope (single-use presentational components, labels, styling, every loading/empty state).
   - **Layer choice:** each row is in the cheapest layer that proves it; browser rows are only important journeys.
   - **Paths and names:** backend `tests/<domain>/test_<operation>_<domain>.py` with manager and API rows of one operation in the same file; pytest names `test_<unit>_<condition>_<expected>`; Vitest and Playwright names are behavior sentences.
   - **Expected results** are concrete and observable.
4. Write `docs/features/<slug>/review/test-plan-review.md`, then reply with one line: `test plan: <n> missing, <n> remove, <n> change`.

## Output file
```markdown
# Review: test plan
| ID | Kind (missing / remove / change) | Row or REQ/EC | Finding | Exact fix (row to add, row to delete, new value) |
|----|----------------------------------|---------------|---------|--------------------------------------------------|
| F-P1 | missing | EC-3 | No test for archiving an already archived site | Add: be-integration `test_archive_site_already_archived_raises_site_not_found_error` in `tests/sites/test_archive_site.py` |
```
Only report real problems. If the plan is fine, write the table with no rows and the line `No findings.`
