---
description: "Spec-first feature workflow. Explore patterns, grill, spec and plan, ONE approval gate, then autonomous implementation, test plan, tests, 4 parallel reviews, up to 3 fix rounds, summary."
disable-model-invocation: true
argument-hint: "[--worktree] <feature description> | resume <slug>"
---

# Feature workflow

Request: `$ARGUMENTS`

**Phase guides are plain files, not skills.** The guides for the grill, the spec, and the test plan live in `.claude/workflow/`. Open them with the Read tool at the paths given below; there is no skill or slash command for them. Convention skills (`*-conventions`, `backend-test-infra`, `git-worktree`) are normal skills: load them with the Skill tool.

**Never stop because a tool refused something.** If a tool call is refused or fails, find another way to do the same step (read the file directly, run the command differently) and continue. Stop only when you need an answer that only the user can give, and only before the gate.

You orchestrate the phases below **in order**. Each phase writes files to `docs/features/<slug>/`. Later phases read those files, not the chat, so keep them accurate. There is **one** human gate (phase 3). Before it, ask as much as needed. After it, **never ask the user anything**. Decide conservatively, log it, and keep going.

---

## Phase 0: Setup
1. If the request is `resume <slug>`: if this session isn't in a worktree but `.claude/worktrees/<slug>/` exists, call `EnterWorktree` with that path first. Then read `docs/features/<slug>/progress.md`, continue from its `Phase:` line, and skip everything already done.
2. Otherwise pick a short kebab-case `<slug>` from the description.
3. **Worktree.** Skip this step if the session is already in a worktree (`git rev-parse --git-dir` differs from `git rev-parse --git-common-dir`). Otherwise load the `git-worktree` skill and create and enter a worktree named `<slug>` when **any** of these holds:
   - the request contains `--worktree` (remove the flag from the description)
   - `docs/features/.active` already exists in this checkout, meaning another feature is in progress here
   - the user answers yes to one question: "Run this feature in its own git worktree, so you can work on other features in parallel?" with the options "Yes, use a worktree (Recommended)" and "No, use this checkout"

   After entering, set up the worktree as the skill describes (dependencies). Everything below happens inside the worktree.
4. Create `docs/features/<slug>/`.
5. Make sure `docs/features/` is in the root `.gitignore`. Add the line if it's missing.
6. Write the slug to `docs/features/.active` (one line). A hook uses it to block tests that aren't in the test plan.
7. Find the base branch: `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`), or `main`. Remember it as `<base>`.
8. Read the root `CLAUDE.md` if it exists (architecture, run and test commands). If it's missing or thin, continue anyway and let `/retro` recommend what to add at the end of the session.

## Phase 1: Explore & discover patterns (mandatory)
Run the `explorer` agent with: the feature description and the feature directory. Wait for it.
Check that `context.md` and `patterns.md` exist and that `patterns.md` has at least one `P-n`. **Don't continue to phase 2 without `patterns.md`.**

## Phase 2: Grill
Read `.claude/workflow/grill-with-docs.md` and follow it fully with the user. It ends when `grill-notes.md` has no open or assumed unknowns and the user has confirmed the readback.

## Phase 3: Spec, plan & ★ GATE
Read `.claude/workflow/write-spec.md`. Write `spec.md` and `plan.md`, run its self-check, and present them for approval.
- On "I have changes", revise and ask again.
- On approval, set `Status: APPROVED (<date>)` in both files, create `progress.md` from `.claude/workflow/templates/progress.md` with every task unchecked, and set `Phase: IMPLEMENT`.
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
Set `Phase: TEST-PLAN`. Read `.claude/workflow/test-plan.md` and write `test-plan.md` from `.claude/workflow/templates/test-plan.md`, covering every REQ, EC, and new code path, with each row in one of the layers `be-unit`, `be-integration`, `be-api`, `fe-unit`, `fe-component`, `fe-integration`, `browser`. For layer guidance, load `backend-test-infra` (backend), and `vitest-conventions` plus `browser-test-conventions` when the frontend is touched.

## Phase 6: Write tests
Set `Phase: TESTS`. Write exactly the planned tests, layer by layer, loading the matching conventions before each layer:
- `be-*`: `pytest-conventions` + `backend-test-infra`
- `fe-component`: `vitest-conventions` + its `references/component-tests.md`
- `fe-integration`: `vitest-conventions` + its `references/integration-tests.md`
- `browser`: `browser-test-conventions`

If the shared frontend test infrastructure is missing (mount helper, MSW server and handlers, factories, the Playwright `fixtures.ts`), create it first, exactly as the skills describe. If the hook blocks a test because it isn't in the plan, add the row to `test-plan.md` first (with a reason), then write the test.
Run each layer and the changed-lines coverage (commands are in the root `CLAUDE.md`): pytest + diff-cover, Vitest + diff-cover, and Playwright. Fix failing tests: when a failure reveals a real bug, fix the code and note it in `progress.md`. Record the results in `test-plan.md` → "Results".

## Phase 7: Review (round 1)
Set `Phase: REVIEW-ROUND-1`. Run these four agents **in parallel**, giving each the feature directory, `<base>`, and the review directory `docs/features/<slug>/review/round-1/`:
`review-conventions` · `review-spec` · `review-bugs` · `review-tests`.
Wait for all four. Each writes `<review directory>/<name>.md`. **Never overwrite or delete an earlier round's files.** They are the review history that `/retro` learns from.

## Phase 8: Triage & fix (max 3 fix rounds)
For round `n` (starting at 1):
1. Read every finding in `review/round-<n>/` and **verify it against the code yourself**. Reviewers can be wrong. Write `review/round-<n>/triage.md`:
   `| Finding | Reviewer | Category | Decision (fix / dismiss) | Reason |`. Dismiss only with a concrete reason (e.g. "false positive: line 40 already checks None").
2. Append one row per reviewer to `review/history.md` (create it with this header the first time):
   `| Round | Reviewer | Blocker | Major | Minor | Fixed | Dismissed | Recurring from earlier round |`
3. If no finding was marked `fix`, go to phase 9.
4. Set `Phase: FIX-ROUND-<n>`. Fix every `fix` finding: blockers first, then majors. Minors are fixed when cheap; otherwise dismiss them with a reason. Re-run the checks and tests.
5. Re-review: re-run **only** the reviewers that had `fix` findings, with the review directory `review/round-<n+1>/` and the previous round's directory, so they can confirm each fix and don't re-raise dismissed findings without new evidence. Set `Phase: REVIEW-ROUND-<n+1>`.
6. Repeat from step 1 for round `n+1`. **Stop after fix round 3**: triage the final review round (steps 1–2), but don't fix it. Remaining findings go into the summary.

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
- Rounds: <n> · Fixed: <n> (by reviewer) · Dismissed: <n> (see `review/round-*/triage.md`, `review/history.md`) · Still open: <list>
## Needs your attention
- <anything still open, risky, or left undone>
```
Apply the final git step from the spec (commit, push, open a PR) only if the spec says so. Delete `docs/features/.active`. Show the user the summary and the path to the feature folder.
