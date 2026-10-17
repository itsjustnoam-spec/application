---
description: "Spec-first feature workflow. Explore patterns, grill, spec and plan, ONE approval gate, then autonomous implementation, test plan, tests, 4 parallel reviews, fix loop, summary."
disable-model-invocation: true
argument-hint: "<feature description> | resume <slug>"
---

# Feature workflow

Request: `$ARGUMENTS`

**Workflow skills are read, not invoked.** `grill-with-docs`, `write-spec`, and `test-plan` are set to `disable-model-invocation: true`, so the Skill tool will refuse them. That's intended: always open them with the Read tool at the paths given below. Convention skills (`*-conventions`, `backend-test-infra`) are normal skills: load them with the Skill tool.

You orchestrate the phases below **in order**. Each phase writes files to `docs/features/<slug>/`. Later phases read those files, not the chat, so keep them accurate. There is **one** human gate (phase 3). Before it, ask as much as needed. After it, **never ask the user anything**. Decide conservatively, log it, and keep going.

---

## Phase 0: Setup
1. If the request is `resume <slug>`: read `docs/features/<slug>/progress.md`, continue from its `Phase:` line, and skip everything already done.
2. Otherwise pick a short kebab-case `<slug>` from the description and create `docs/features/<slug>/`.
3. Make sure `docs/features/` is in the root `.gitignore`. Add the line if it's missing.
4. Write the slug to `docs/features/.active` (one line). A hook uses it to block tests that aren't in the test plan.
5. Find the base branch: `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`), or `main`. Remember it as `<base>`.
6. Read the root `CLAUDE.md` if it exists (architecture, run and test commands). If it's missing or thin, continue anyway and let `/retro` recommend what to add at the end of the session.

## Phase 1: Explore & discover patterns (mandatory)
Run the `explorer` agent with: the feature description and the feature directory. Wait for it.
Check that `context.md` and `patterns.md` exist and that `patterns.md` has at least one `P-n`. **Don't continue to phase 2 without `patterns.md`.**

## Phase 2: Grill
Read `.claude/skills/grill-with-docs/SKILL.md` and follow it fully with the user. It ends when `grill-notes.md` has no open or assumed unknowns and the user has confirmed the readback.

## Phase 3: Spec, plan & ★ GATE
Read `.claude/skills/write-spec/SKILL.md`. Write `spec.md` and `plan.md`, run its self-check, and present them for approval.
- On "I have changes", revise and ask again.
- On approval, set `Status: APPROVED (<date>)` in both files, create `progress.md` from `.claude/skills/write-spec/templates/progress.md` with every task unchecked, and set `Phase: IMPLEMENT`.
- Apply the git strategy from the spec (e.g. create the branch).

From here on: **no questions to the user.**

## Phase 4: Implement
For each task in `plan.md`, in order:
1. Open the task's pattern reference file and mirror its structure.
2. Load the relevant conventions skill (`python-conventions` / `vue-conventions`) before writing code in that stack.
3. Implement the task. The post-edit hook reports convention and lint problems after every edit. Fix them immediately.
4. Run the task's `Verify` command, plus the existing tests of the touched service (regressions only: don't write new tests yet). For Python, also run `uv run mypy --strict` on the changed package, and ignore only "missing return type annotation" errors on functions that return nothing.
5. Tick the task in `progress.md` and record the check results. Commit if the git strategy says "per task".
6. If the spec doesn't cover a situation, choose the most conservative option consistent with the spec, add a `DEV-n` line under "Deviations", and continue.

If a task can't be completed (e.g. a broken environment), record why in `progress.md`, skip only what depends on it, and carry on.

## Phase 5: Test plan
Set `Phase: TEST-PLAN`. Read `.claude/skills/test-plan/SKILL.md` and write `test-plan.md` from its template (`.claude/skills/test-plan/templates/test-plan.md`), covering every REQ, EC, and new code path, with each row in one of the layers `be-unit`, `be-integration`, `be-api`, `fe-unit`, `fe-component`, `fe-integration`, `browser`. For layer guidance, load `backend-test-infra` (backend), and `vitest-conventions` plus `browser-test-conventions` when the frontend is touched.

## Phase 6: Write tests
Set `Phase: TESTS`. Write exactly the planned tests, layer by layer, loading the matching conventions before each layer:
- `be-*`: `pytest-conventions` + `backend-test-infra`
- `fe-component`: `vitest-conventions` + its `references/component-tests.md`
- `fe-integration`: `vitest-conventions` + its `references/integration-tests.md`
- `browser`: `browser-test-conventions`

If the shared frontend test infrastructure is missing (mount helper, MSW server and handlers, factories, the Playwright `fixtures.ts`), create it first, exactly as the skills describe. If the hook blocks a test because it isn't in the plan, add the row to `test-plan.md` first (with a reason), then write the test.
Run each layer and the changed-lines coverage (commands are in the root `CLAUDE.md`): pytest + diff-cover, Vitest + diff-cover, and Playwright. Fix failing tests: when a failure reveals a real bug, fix the code and note it in `progress.md`. Record the results in `test-plan.md` → "Results".

## Phase 7: Review
Set `Phase: REVIEW`. Run these four agents **in parallel**, each with the feature directory and `<base>`:
`review-conventions` · `review-spec` · `review-bugs` · `review-tests`.
Wait for all four. Each writes `review/<name>.md`.

## Phase 8: Triage & fix (max 2 rounds)
1. Read every finding and **verify it against the code yourself**. Reviewers can be wrong. Write `review/triage.md`:
   `| Finding | Decision (fix / dismiss) | Reason |`. Dismiss only with a concrete reason (e.g. "false positive: line 40 already checks None").
2. Fix every `fix` finding: blockers first, then majors. Minors are fixed when cheap; otherwise dismiss them with a reason. Re-run the checks and tests.
3. Re-run **only** the reviewers that had `fix` findings. Set `Phase: FIX-ROUND-<n>`.
4. Stop after round 2 even if findings remain. They go into the summary.

## Phase 9: Summary
Set `Phase: DONE`. Write `summary.md`:
```markdown
# Summary: <feature>
## Built
- REQ-1 … (where)
## Deviations
- DEV-n …
## Tests
- <n> tests per layer · changed-line coverage: backend <n>%, frontend <n>% · browser: <passed>/<total>
## Review
- Fixed: <n> (by reviewer) · Dismissed: <n> (see triage.md) · Still open: <list>
## Needs your attention
- <anything still open, risky, or left undone>
```
Apply the final git step from the spec (commit, push, open a PR) only if the spec says so. Delete `docs/features/.active`. Show the user the summary and the path to the feature folder.
