---
description: "Spec-first feature workflow. Explore patterns with three explorers, grill, spec and plan, ONE approval gate, then autonomous implementation, test plan with a one-pass review, tests, parallel reviews (two for conventions, one for quality, optionally one in the browser), up to 3 fix rounds, summary, push."
disable-model-invocation: true
argument-hint: "[--no-worktree] <Jira issue> <feature description> | resume <branch>"
---

# Feature workflow

Request: `$ARGUMENTS`

**Where things live.** This workflow is installed in `~/.claude/` (the home directory's `.claude` folder). In a shell, that's `$HOME/.claude`; for the Read tool, expand it to the absolute path. The feature folder (`docs/features/`) and worktrees (`.claude/worktrees/`) belong to the project you're working in.

**Phase guides are plain files, not skills.** The guides for the grill, the spec, and the test plan live in `~/.claude/workflow/`. Open them with the Read tool at the paths given below; there is no skill or slash command for them. Convention skills (`*-conventions`, `backend-test-infra`, `git-worktree`) are normal skills: load them with the Skill tool.

**Never stop because a tool refused something.** If a tool call is refused or fails, find another way to do the same step (read the file directly, run the command differently) and continue. Stop only when you need an answer that only the user can give, and only before the gate.

**Run to the end.** After the gate, a Stop hook won't let you end your turn until `progress.md` says `Phase: DONE`. Don't write a "final report" before then, and don't stop to ask for something in the middle. Only when you're genuinely blocked (a broken environment, or a decision the spec can't answer) write `BLOCKED: <reason>` in `progress.md` and stop. If the user tells you to stop, write `BLOCKED: stopped by user` first.

**After a context compaction**, or whenever you're unsure where you are, re-read `progress.md` and continue from its `Phase:` line.

**Only the code you write follows the conventions.** New and changed lines follow the convention skills, even when the code around them doesn't. **Never change an existing line the task doesn't need**, even when it breaks a convention: no reformatting, renaming, re-dating, or "fixing" old code, also in files you add code to. The checks only report lines this branch wrote, so leave everything else as it is. Two exceptions:
- In a `.vue` file you add code to, fix the structure rules in the whole file: `Props` / `Emits` interfaces in `<script lang="ts">`, constants out of `<script setup>`, no exports.
- Changing existing code so it can be reused instead of duplicated (one more parameter, a generic type) is allowed, when that's how the plan or a review says to avoid duplication.

**No code comments.** Not in code, not in tests, not in templates or styles.

**Write files with the Write or Edit tools**, never with shell heredocs or redirects. The hooks only check files written through Write/Edit.

You orchestrate the phases below **in order**. Each phase writes files to `docs/features/<slug>/`. Later phases read those files, not the chat, so keep them accurate. There is **one** human gate (phase 3). Before it, ask as much as needed. After it, **never ask the user anything**. Decide conservatively, log it as a `DEV-n` line under "Deviations" in `progress.md`, and keep going.

---

## Phase 0: Setup
1. If the request is `resume <slug>`: if this session isn't in a worktree but `.claude/worktrees/<slug>/` exists, call `EnterWorktree` with that path first. Then read `docs/features/<slug>/progress.md`, delete its `BLOCKED:` line if there is one, continue from its `Phase:` line, and skip everything already done.
2. Otherwise build `<slug>`, which is also the branch name, as `~/.claude/CLAUDE.md` → Git says: `BTRC-<JIRA-ISSUE>-<what-we-do>` in kebab case. Take the Jira issue from the request. If it isn't there, ask the user for it (one question). The feature folder, the worktree folder, and the branch all use this name.
3. Find the base branch: `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`), or `main`. Call it `<base branch>`. Run `git fetch origin`, so the branch starts from the latest code.
4. **Worktree (the default).** Skip this step if the session is already in a worktree (`git rev-parse --git-dir` differs from `git rev-parse --git-common-dir`) or the request contains `--no-worktree` (remove the flag from the description). Otherwise load the `git-worktree` skill, create the worktree for `<slug>` from `origin/<base branch>`, enter it, and set it up (dependencies) as the skill describes. Everything below happens inside the worktree. With `--no-worktree`, create and switch to the branch `<slug>` from `origin/<base branch>` in this checkout.
5. Create `docs/features/<slug>/`. Make sure `docs/features/` is in the root `.gitignore`; add the line if it's missing.
6. Write the slug to `docs/features/.active` (one line). The hooks use it to find the feature.
7. Create `docs/features/<slug>/progress.md` from `~/.claude/workflow/templates/progress.md`. Set `Phase: EXPLORE`, and fill in `Base:` with the output of `git merge-base HEAD origin/<base branch>` (a commit SHA), `Base branch:`, and `Worktree:`. **`<base>` below always means that `Base:` SHA.** The checks and reviewers diff against it, so they see exactly what this branch changed.
8. Read the root `CLAUDE.md` if it exists (architecture, run and test commands). If it's missing or thin, continue anyway and let `/retro` recommend what to add at the end of the session.

## Phase 1: Explore & discover patterns (mandatory)
Run **three** `explorer` agents **in parallel**, all with the same task: the feature description and their own output directory (`docs/features/<slug>/explore-1/`, `explore-2/`, `explore-3/`). Wait for all three.

Then **merge** their files into `docs/features/<slug>/context.md` and `patterns.md`, in the same formats. Group the patterns by reference file:
- **Found by two or three explorers:** keep it, after checking that its reference file exists. Combine their notes on its shape into one `P-n`.
- **Found by only one:** open the reference file yourself. Keep the pattern when the file exists and fits the feature; drop it otherwise.
- **Explorers disagree** (different reference files or different shapes for the same kind of change): record it as an inconsistency `I-n` for the grill.
- **Context, reusable code, and inconsistencies:** combine all three lists, without duplicates. A tool counts as missing if any explorer reports it missing and you confirm it.
- End `patterns.md` with `## Explorer agreement`: what only one explorer found, and every disagreement.

Keep `explore-1/` to `explore-3/` (`/retro` learns from them). Check that `context.md` and `patterns.md` exist and that `patterns.md` has at least one `P-n`. **Don't continue to phase 2 without `patterns.md`.** Set `Phase: GRILL`.

## Phase 2: Grill
Read `~/.claude/workflow/grill-with-docs.md` and follow it fully with the user. It ends when `grill-notes.md` has no open or assumed unknowns and the user has confirmed the readback. Set `Phase: SPEC`.

## Phase 3: Spec, plan & ★ GATE
Read `~/.claude/workflow/write-spec.md`. Write `spec.md` and `plan.md`, run its self-check, and present them for approval.
- On "I have changes", revise and ask again.
- On approval, set `Status: APPROVED (<date>)` in both files, add every task to `progress.md` unchecked, fill in its `Push:` and `Playwright check:` lines from the spec, and set `Phase: IMPLEMENT`.

From here on: **no questions to the user.**

## Phase 4: Implement
**Load each conventions skill the first time a task needs it, and don't load it again for later tasks.** After a context compaction, load it once more. Use `python-conventions` for Python, `vue-conventions` for the frontend, and `sql-conventions` when a task touches a table model, a database session, or a migration.

For each task in `plan.md`, in order:
1. Open the task's pattern reference file and mirror its structure. Use the existing code the plan says to reuse instead of writing it again.
2. Implement the task. The post-edit hook reports convention and lint problems on the lines you just wrote. Fix them immediately, and only them.
3. Run the task's `Verify` command and the existing tests of the touched service (regressions only: don't write new tests yet). **Tests run only on this branch's own services**: before the first test run, start them as `git-worktree` §3 describes and record them in `progress.md`. Never point tests at a database or service that was already running.
4. Run the checks on the files you changed and fix everything they report (they report only lines this branch wrote):
   - `python ~/.claude/scripts/lint_changed.py --since auto <changed files>` (the convention checkers and eslint)
   - for Python, from the service's directory: `python ~/.claude/scripts/mypy_strict.py --since auto <package>`
5. When the change legitimately breaks an existing test (the behavior was meant to change), update that test now, without adding new test functions, and log a `DEV-n`.
6. Tick the task in `progress.md` and record the check results. Commit if the git strategy says "per task".
7. If the spec doesn't cover a situation, choose the most conservative option consistent with the spec, add a `DEV-n` line under "Deviations", and continue.

If a task can't be completed (e.g. a broken environment), record why in `progress.md`, skip only what depends on it, and carry on.

## Phase 5: Test plan
Set `Phase: TEST-PLAN`. Read `~/.claude/workflow/test-plan.md` and write `test-plan.md` from `~/.claude/workflow/templates/test-plan.md`, covering every REQ, EC, and new code path, with each row in one of the layers `be-unit`, `be-integration`, `be-api`, `fe-unit`, `fe-component`, `fe-integration`. Plan `browser` rows only when the user asked for browser tests in the grill. For layer guidance, load `backend-test-infra` (backend), and `vitest-conventions` when the frontend is touched.

**Test-plan review (one pass).** Run the `review-test-plan` agent once with the feature directory. It writes `review/test-plan-review.md`. Apply every finding you agree with to `test-plan.md`. For each one you don't apply, add a reason in that file. There is no second review round: continue to phase 6.

## Phase 6: Write tests
Set `Phase: TESTS`. Write exactly the planned tests, layer by layer, loading the matching conventions before each layer (once, as in phase 4):
- `be-*`: `pytest-conventions` + `backend-test-infra`
- `fe-component`: `vitest-conventions` + its `references/component-tests.md`
- `fe-integration`: `vitest-conventions` + its `references/integration-tests.md`
- `browser` (only when planned): `browser-test-conventions`

If the hook blocks a test because it isn't in the plan, add the row to `test-plan.md` first (with a reason), then write the test.
Run each layer on this branch's own services (commands are in the root `CLAUDE.md`): pytest + diff-cover (backend changed-line coverage, as a report), Vitest, and Playwright when planned. Then run `python ~/.claude/scripts/lint_changed.py --since auto` on every changed file (`git diff --name-only <base>` plus untracked files) and `mypy_strict.py --since auto` on every changed Python package, and fix everything they report. Every uncovered changed backend line is either tested or listed as exempt in `test-plan.md`. Fix failing tests: when a failure reveals a real bug, fix the code and note it in `progress.md`. Record the results in `test-plan.md` → "Results".

## Phase 7: Review (round 1)
Set `Phase: REVIEW-ROUND-1`.

**Before each review round**, run every planned test layer and the diff-cover report, and write the output to `<review directory>/test-run.txt`. `review-tests` reads it instead of running everything again.

**Split the conventions work between two reviewers, by whole skills:**
- reviewer 1, the code skills: `python-conventions`, `sql-conventions`, `vue-conventions`
- reviewer 2, the test skills: `pytest-conventions`, `backend-test-infra`, `vitest-conventions`, `browser-test-conventions`

Leave out skills that apply to no changed file (see the file table in `review-conventions`). If one list ends up empty, run only the other reviewer. Record both lists in `progress.md`, so later rounds reuse them.

Run these agents **in parallel**, giving each the feature directory, `<base>`, and the review directory `docs/features/<slug>/review/round-1/`:
- `review-conventions` twice: as reviewer 1 and as reviewer 2, each with its skill list
- `review-spec` · `review-bugs` · `review-tests` · `review-quality`
- `review-ui`, only when `progress.md` says `Playwright check: yes` and the frontend changed. First start the app on this branch's own services (the backend on the containers from `git-worktree` §3, and the frontend dev server on a free port), then give the agent the frontend URL. Stop the app after the round.

Wait for all of them. Each writes `<review directory>/<name>-review.md` (`conventions-1-review.md`, `conventions-2-review.md`, `spec-review.md`, `bugs-review.md`, `tests-review.md`, `quality-review.md`, `ui-review.md`). In triage and `history.md`, `conventions-1` and `conventions-2` are two separate reviewers. **Never overwrite or delete an earlier round's files.** They are the review history that `/retro` learns from.

## Phase 8: Triage & fix (max 3 fix rounds)
For round `n` (starting at 1):
1. Read every finding in `review/round-<n>/` and **verify it against the code yourself**. Reviewers can be wrong. Write `review/round-<n>/triage.md`:
   `| Finding | Reviewer | Category | Decision (fix / dismiss / open) | Reason |`. **Write the triage file before fixing anything.**
   - Use `fix` or `dismiss`. There is no "defer", "later", or "out of scope".
   - Dismiss only with a concrete reason that the finding is wrong, e.g. "false positive: line 40 already checks None", or "contradicts spec D-3". These are **not** valid reasons: "it's a refactor", "it's minor", "it matches the existing code", "it's out of scope". A finding that shows a convention or spec violation in code this branch wrote is fixed.
   - A finding about an existing line the branch didn't change is dismissed ("not written by this branch"), unless it's a `SCOPE` finding (the branch changed a line it didn't need to), which is fixed by reverting the change.
   - `open` is allowed **only in the final round** (step 6): a valid finding that isn't fixed because of the round limit.
2. Append one row per reviewer to `review/history.md` (create it with this header the first time):
   `| Round | Reviewer | Blocker | Major | Minor | Fixed | Dismissed | Open | Recurring from earlier round |`
3. If no finding was marked `fix`, go to phase 9.
4. Set `Phase: FIX-ROUND-<n>`. Fix every `fix` finding: blockers first, then majors, then minors. A fix that needs a new test gets its `test-plan.md` row first. Then run the checks of phase 4 step 4 and every test layer again, on everything the fixes touched.
5. Re-review: re-run the reviewers that had `fix` findings (a conventions reviewer with the same number and skill list as before), plus `review-quality` whenever the fixes changed code, with the review directory `review/round-<n+1>/` and the previous round's directory, so they can confirm each fix and don't re-raise dismissed findings without new evidence. Write `test-run.txt` first. Set `Phase: REVIEW-ROUND-<n+1>`.
6. Repeat from step 1 for round `n+1`. **Stop after fix round 3**: triage the final review round (steps 1–2), marking each valid finding `open`, but don't fix it.

## Phase 9: Summary
Write `summary.md`:
```markdown
# Summary: <feature>
## Built
- REQ-1 … (where)
## Deviations
- DEV-n …
## Tests
- <n> tests per layer · backend changed-line coverage: <n>% · browser: <passed>/<total> or not planned
## Review
- Rounds: <n> · Fixed: <n> (by reviewer) · Dismissed: <n> (see `review/round-*/triage.md`, `review/history.md`)
## Open problems
- <every finding marked `open`, with its ID, file:line, and what's wrong> (or "None")
## Needs your attention
- <anything else still risky, or left undone>
```
Then set `Phase: DONE` and do the git step:
1. Commit everything the spec's git strategy says to commit.
2. If `progress.md` says `Push: yes` (decided in the grill): push the branch (`git push -u origin <slug>`) and open the merge request if the spec says so. Then follow the pipeline through the GitLab MCP server, if one is connected: wait for it to finish, and when a job fails, read its log, fix the cause, run the checks and tests again, commit, push, and check again. Stop when the pipeline passes, or after 3 failed fix attempts, and report what's left. If no GitLab MCP server is connected, say so and stop after pushing. Don't ask the user anything here: the grill already decided.
3. If it says `Push: no`, leave the work committed and tell the user the branch name.
4. Stop this branch's own Docker services (`git-worktree` §3, step 7).

Delete `docs/features/.active` when the git step is done. Show the user the summary, **including every open problem**, and the path to the feature folder.
