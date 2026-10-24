---
description: "Spec-first feature workflow. Explore patterns with three explorers, grill, spec and plan, ONE approval gate, then autonomous implementation, test plan with a one-pass review, tests, parallel reviews (general, tests, conventions, and optionally the UI in the browser), up to 3 fix rounds, summary, push."
disable-model-invocation: true
argument-hint: "[--no-worktree] <Jira issue> <feature description> | resume <branch>"
---

# Feature workflow

Request: `$ARGUMENTS`

**Where things live.** This workflow is installed in `~/.claude/` (the home directory's `.claude` folder). In a shell, that's `$HOME/.claude`; for the Read tool, expand it to the absolute path. The feature folder (`docs/features/`) and worktrees (`.claude/worktrees/`) belong to the project you're working in.

**Phase guides are plain files, not skills.** The guides for the grill, the spec, and the test plan live in `~/.claude/workflow/`. Open them with the Read tool at the paths given below; there is no skill or slash command for them. Convention skills (`*-conventions`, `backend-test-infra`, `git-worktree`) are normal skills: load them with the Skill tool.

**Never stop because a tool refused something.** If a tool call is refused or fails, find another way to do the same step (read the file directly, run the command differently) and continue. Stop only when you need an answer that only the user can give, and only before the gate.

**Run to the end.** After the gate, a Stop hook won't let you end your turn until `progress.md` says `Phase: DONE`. Don't write a "final report" before then, and don't stop to ask for something in the middle. Only when you're genuinely blocked (a broken environment, or a decision the spec can't answer) write `BLOCKED: <reason>` in `progress.md` and stop. If the user tells you to stop, write `BLOCKED: stopped by user` first.

**After a context compaction**, or whenever you're unsure where you are, re-read `progress.md`, this file (`~/.claude/commands/feature.md`), and the guide of the current phase (`grill-with-docs.md`, `write-spec.md`, or `test-plan.md` in `~/.claude/workflow/`), then continue from the `Phase:` line.

**Only the code you write follows the conventions.** New and changed lines follow the convention skills, even when the code around them doesn't. **Never change an existing line the task doesn't need**, even when it breaks a convention: no reformatting, renaming, re-dating, or "fixing" old code, also in files you add code to. The checks only report lines this branch wrote, so leave everything else as it is. Two exceptions:
- In a `.vue` file you add code to, fix the structure rules in the whole file: `Props` / `Emits` interfaces in `<script lang="ts">`, constants out of `<script setup>`, no exports.
- Changing existing code so it can be reused instead of duplicated (one more parameter, a generic type) is allowed, when that's how the plan or a review says to avoid duplication.

**No code comments.** Not in code, not in tests, not in templates or styles. Python's section banners (`# ----- Imports ----- #`) aren't comments: keep them where `python-conventions` requires them.

**Write files with the Write or Edit tools**, never with shell heredocs or redirects. The hooks only check files written through Write/Edit.

**Running agents.** Call the Agent tool once per agent, with `subagent_type` set to the agent's name (`explorer`, `general-reviewer`, ...). Never use a general-purpose agent in place of a named one. Agents that run in parallel are all called in **one** message. Every agent prompt gives literal values, never "see progress.md": the feature directory, the `Base:` SHA, the review directory, and `<Claude home>` (the absolute path of `~/.claude`, from `echo $HOME/.claude`). Every agent prompt also includes this rule, word for word: "**Find code with graphify first.** When `graphify-out/graph.json` exists, run `graphify query "<question>"` before your first grep, search, or source-file read; use `graphify path "<A>" "<B>"` for how two things connect, `graphify explain "<name>"` for one function or class, and `graphify affected "<name>"` for what a change impacts. Read files only for the lines the graph pointed to; grep only when the graph has no answer."

You orchestrate the phases below **in order**. Each phase writes files to `docs/features/<slug>/`. Later phases read those files, not the chat, so keep them accurate. There is **one** human gate (phase 3). Before it, ask as much as needed. After it, **never ask the user anything**. Decide conservatively, log it as a `DEV-n` line under "Deviations" in `progress.md`, and keep going.

---

## Phase 0: Setup
1. If the request is `resume <slug>`: if this session isn't in a worktree but `.claude/worktrees/<slug>/` exists, call `EnterWorktree` with that path first. Then read `docs/features/<slug>/progress.md`, delete its `BLOCKED:` line if there is one, continue from its `Phase:` line, and skip everything already done.
2. Otherwise build `<slug>`, which is also the branch name, as `~/.claude/CLAUDE.md` → Git says: `BTRC-<JIRA-ISSUE>-<what-we-do>` in kebab case. Take the Jira issue from the request. If it isn't there, ask the user for it (one question). The feature folder, the worktree folder, and the branch all use this name.
3. Find the base branch: `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`), or `main`. Call it `<base branch>`. Run `git fetch origin`, so the branch starts from the latest code. If the repository has no `origin` remote (`git remote` prints nothing), use the local `<base branch>` instead of `origin/<base branch>` everywhere below, and write `No origin: using the local <base branch>` under "Deviations".
4. **Worktree (the default).** Skip this step if the session is already in a worktree (`git rev-parse --git-dir` differs from `git rev-parse --git-common-dir`) or the request contains `--no-worktree` (remove the flag from the description). Otherwise load the `git-worktree` skill, create the worktree for `<slug>` from `origin/<base branch>`, enter it, and set it up (dependencies) as the skill describes. Everything below happens inside the worktree. With `--no-worktree`, create and switch to the branch `<slug>` from `origin/<base branch>` in this checkout.
5. Create `docs/features/<slug>/`. Make sure `docs/features/` is in the root `.gitignore`; add the line if it's missing.
6. Write the slug to `docs/features/.active` (one line). The hooks use it to find the feature.
   **Graph:** if `graphify` is installed (`graphify --help` works), run `graphify update .` in the checkout root (code only, a few seconds), so the explorers start from a current graph. Without graphify, skip this and the agents grep as usual.
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
- Open at most 10 reference files yourself. When more patterns were found by only one explorer, keep the 10 closest to the feature and list the rest under "Explorer agreement" as not verified.

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
3. Run the task's `Verify` command and the existing tests of the touched service (regressions only: don't write new tests yet). **Tests use only the compose project named after this branch.** Before the first test run, load the `git-worktree` skill (also when you're not in a worktree, and again after a compaction) and follow its §3 "Docker services": use the project if it's running, or create it from the project's own compose file. Fill in the "Test services" and "Test commands" sections of `progress.md`. Never point tests at any other container.
4. Run the checks on the files you changed and fix everything they report (they report only lines this branch wrote):
   - `python ~/.claude/scripts/lint_changed.py --since auto <changed files>` (the convention checkers and eslint)
   - for Python, from the service's directory: `python ~/.claude/scripts/mypy_strict.py --since auto <package>`. Exit code 2 with "mypy could not run" means mypy isn't installed in that service: add it with `uv add --dev mypy`, log a `DEV-n`, and run it again.
5. When the change legitimately breaks an existing test (the behavior was meant to change), update that test now, without adding new test functions, and log a `DEV-n`.
6. Tick the task in `progress.md` and record the check results. Commit if the git strategy says "per task".
7. If the spec doesn't cover a situation, choose the most conservative option consistent with the spec, add a `DEV-n` line under "Deviations", and continue.

If a task can't be completed (e.g. a broken environment), record why in `progress.md`, skip only what depends on it, and carry on.

## Phase 5: Test plan
Set `Phase: TEST-PLAN`. Read `~/.claude/workflow/test-plan.md` and write `test-plan.md` from `~/.claude/workflow/templates/test-plan.md`, covering every REQ, EC, and new code path, with each row in one of the layers `be-unit`, `be-integration`, `be-api`, `fe-unit`, `fe-component`, `fe-integration`. There are no `browser` (Playwright) tests for now. For layer guidance, load `backend-test-infra` (backend), and `vitest-conventions` when the frontend is touched.

**Test-plan review (one pass).** Run the `review-test-plan` agent once with the feature directory and `<Claude home>`. It writes `review/test-plan-review.md`. Apply every finding you agree with to `test-plan.md`. For each one you don't apply, add a reason in that file. There is no second review round: continue to phase 6.

## Phase 6: Write tests
Set `Phase: TESTS`. Write exactly the planned tests, layer by layer, loading the matching conventions before each layer (once, as in phase 4):
- `be-*`: `pytest-conventions` + `backend-test-infra`
- `fe-component`: `vitest-conventions` + its `references/component-tests.md`
- `fe-integration`: `vitest-conventions` + its `references/integration-tests.md`

If the hook blocks a test because it isn't in the plan, add the row to `test-plan.md` first (with a reason), then write the test.
Run each layer with the "Test commands" of `progress.md`, on this branch's compose project: `uv run pytest --cov=<package> --cov-report=xml`, then `uv run diff-cover coverage.xml --compare-branch=<base>` (backend changed-line coverage, as a report), and `npx vitest run` for the frontend. Then run `python ~/.claude/scripts/lint_changed.py --since auto` on every changed file (`git diff --name-only <base>` plus untracked files) and `mypy_strict.py --since auto` on every changed Python package, and fix everything they report. Every uncovered changed backend line is either tested or listed as exempt in `test-plan.md`. Fix failing tests: when a failure reveals a real bug, fix the code and note it in `progress.md`. Record the results in `test-plan.md` → "Results".

## Phase 7: Review (round 1)
Set `Phase: REVIEW-ROUND-1`.

**The rounds, in order:** review 1 → triage 1 → fix 1 → review 2 → triage 2 → fix 2 → review 3 → triage 3 → fix 3 → review 4 → triage 4. Review 4 is the last: its triage marks each valid finding `open` and fixes nothing. Every earlier triage uses only `fix` and `dismiss`.

**Every review round runs the same way:**
1. **Checks first, once.** Write `<review directory>/checks.txt` with the full output of:
   - the "Test commands" of `progress.md` (every test layer, and the diff-cover report)
   - `python ~/.claude/scripts/lint_changed.py --since <base> <every changed file>` (the convention checkers and eslint, on the lines the branch wrote)
   - `python ~/.claude/scripts/mypy_strict.py --since <base> <package>`, from each changed Python service's directory

   The reviewers read this file and never run these tools themselves, so they all start from the same results.
2. Run the reviewers below **in parallel, in one message**.
3. Wait for all of them, then go to phase 8 for the triage.

**The reviewers.** Give each one the feature directory, `<base>`, `<Claude home>`, and the review directory (`docs/features/<slug>/review/round-1/`), as literal values, plus the skill list where it has one. For example, `tests-reviewer` gets: "Skills: pytest-conventions, backend-test-infra. Feature directory: docs/features/BTRC-1234-add-authentication/. Base: 3f2a…. Claude home: /home/you/.claude. Review directory: docs/features/BTRC-1234-add-authentication/review/round-1/."

| Agent | Runs | Writes | Checks |
|---|---|---|---|
| `general-reviewer` | always | `general-review.md` | The code against the spec (REQs, edge cases, contracts, scope, deviations), runtime bugs, and duplicated or unused code |
| `tests-reviewer` | always (missing tests are its findings) | `tests-review.md` | Code the tests don't cover, tests that check nothing or break the rules, and the test-convention checklists. Skills: the ones of `pytest-conventions`, `backend-test-infra`, `vitest-conventions` that apply to the changed test files |
| `conventions-reviewer` | when application code changed | `conventions-review.md` | Every non-test convention on the lines the branch wrote, pattern adherence, suppressions, private members, and old lines changed only to apply a convention. Skills: the ones of `python-conventions`, `sql-conventions`, `vue-conventions` that apply to the changed files |
| `ui-reviewer` | only when `progress.md` says `Playwright check: yes` and the frontend changed | `ui-review.md` | The UI and UX of the spec's journeys in the browser |

Record the two skill lists in `progress.md`, so later rounds reuse them. Before `ui-reviewer`, start the app on this branch's compose project (the backend on its containers from `git-worktree` §3, the frontend dev server on a free port), give the agent the frontend URL, and stop the app after the round.

**Never overwrite or delete an earlier round's files.** They are the review history that `/retro` learns from.

## Phase 8: Triage & fix (max 3 fix rounds)
For round `n` (starting at 1):
1. Read every finding in `review/round-<n>/` and **verify it against the code yourself**. Reviewers can be wrong. Write `review/round-<n>/triage.md`:
   `| Finding | Reviewer | Category | Decision (fix / dismiss / open) | Reason |`. **Write the triage file before fixing anything.**
   - Use `fix` or `dismiss`. There is no "defer", "later", or "out of scope".
   - Dismiss only with a concrete reason that the finding is wrong, e.g. "false positive: line 40 already checks None", or "contradicts spec D-3". These are **not** valid reasons: "it's a refactor", "it's minor", "it matches the existing code", "it's out of scope". A finding that shows a convention or spec violation in code this branch wrote is fixed.
   - A finding about an existing line the branch didn't change is dismissed ("not written by this branch"), unless it's a `SCOPE` finding (the branch changed a line it didn't need to), which is fixed by reverting the change.
   - `open` is allowed **only in triage 4**, after review 4 (step 6): a valid finding that isn't fixed because of the round limit. In triage 4, `fix` isn't allowed.
2. Append one row per reviewer to `review/history.md` (create it with this header the first time):
   `| Round | Reviewer | Blocker | Major | Minor | Fixed | Dismissed | Open | Recurring from earlier round |`
3. If no finding was marked `fix`, go to phase 9.
   Changes to `graphify-out/` are expected in every branch (the graph is committed and updated after code changes). Dismiss any finding about them.
4. Set `Phase: FIX-ROUND-<n>`. Fix every `fix` finding: blockers first, then majors, then minors. A fix that needs a new test gets its `test-plan.md` row first. Then run the checks of phase 4 step 4 and every test layer again, on everything the fixes touched.
5. Set `Phase: REVIEW-ROUND-<n+1>` and run review round `n+1` the same way as phase 7 (`checks.txt` first), with the review directory `review/round-<n+1>/` and the previous round's directory. Re-run a reviewer when it had `fix` findings, or when the fixes touched its area: application code for `general-reviewer` and `conventions-reviewer`, tests for `tests-reviewer`, the frontend for `ui-reviewer`. Each gets the same skill list as before. They confirm each fix and don't re-raise dismissed findings without new evidence.
6. Repeat from step 1 for round `n+1`. After fix 3 comes review 4 and triage 4: mark each valid finding `open`, fix nothing, and go to phase 9.

## Phase 9: Summary and git
Set `Phase: SUMMARY` and write `summary.md`:
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
Then set `Phase: GIT` and do the git step. The Stop hook keeps you going until `Phase: DONE`, so don't set it before the last step:
1. Commit everything the spec's git strategy says to commit.
2. If `progress.md` says `Push: yes` (decided in the grill): push the branch (`git push -u origin <slug>`) and open the merge request if the spec says so. Then follow the pipeline through the GitLab MCP server, if one is connected: wait for it to finish, and when a job fails, read its log, fix the cause, run the checks and tests again, commit, push, and check again. Stop when the pipeline passes, or after 3 failed fix attempts, and report what's left. If no GitLab MCP server is connected, say so and stop after pushing. Don't ask the user anything here: the grill already decided.
3. If it says `Push: no`, leave the work committed and tell the user the branch name.
4. Remove this branch's compose project: `docker compose -p <Compose project from progress.md> down -v` (`git-worktree` §3, step 8).
5. Delete `docs/features/.active`.
6. Set `Phase: DONE` as the very last change. Show the user the summary, **including every open problem**, and the path to the feature folder.
