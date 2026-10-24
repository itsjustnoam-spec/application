# Claude Code workflow (user-level, `~/.claude`)

A spec-first Claude Code workflow for Vue/Vuetify + FastAPI microservice projects. It's installed in `~/.claude/` (on Ubuntu, `/home/<you>/.claude/`), so Claude Code loads its skills, agents, commands, and hooks in every project. This repo's `.claude/` folder is its source. Feature files (`docs/features/`) and worktrees (`.claude/worktrees/`) still live in each project.

```
/feature <Jira issue> "<what you want>"
  0 Setup: fetch, a worktree for the branch BTRC-<issue>-<what>, progress.md with the base commit
  1 Explore: three explorers with the same task, merged by vote → context.md, patterns.md
  2 Grill: questions with recommendations, one round of "I'm going to use X, agree?", push yes/no, Playwright check yes/no → grill-notes.md
  3 Spec + plan (key details for the key parts) → ★ you approve (the only stop)
  4 Implement task by task (hooks check the lines just written)
  5 Test plan → test-plan.md, reviewed once by review-test-plan (a hook blocks tests that aren't in it)
  6 Write tests on the branch's own Docker services + changed-line coverage report
  7 Review in parallel: conventions ×2 (code skills / test skills) · spec · bugs · tests · quality · ui (optional, Playwright)
  8 Triage + fix (max 3 rounds; every round kept in review/round-<n>/)
  9 summary.md with every open problem, then push and follow the pipeline (if you said yes in the grill), remove the branch's compose project, Phase: DONE
```

Everything for a feature lives in `docs/features/<slug>/` (git-ignored). Resume an interrupted run with `/feature resume <slug>`.

**Only the code a branch writes is checked.** The hooks, the checkers, and the reviewers look only at lines the branch added or changed (against the `Base:` commit in `progress.md`), so Claude never "fixes" old code it didn't write. The one exception: in a `.vue` file the branch changed, the structure rules (`Props`/`Emits` interfaces in `<script lang="ts">`, constants out of `<script setup>`, no exports) apply to the whole file.

---

## Layout

| Path | What |
|---|---|
| `CLAUDE.md` | General working rules loaded in every session (think first, keep it simple, surgical changes, no comments, no suppressions, own test services, branch names, pushing) |
| `settings.json` | Hooks: post-edit check of the lines just written, test-plan guard, and a Stop hook that keeps a run going until `Phase: DONE` |
| `install.sh` | Copies the workflow into `~/.claude/` and merges the hooks into `~/.claude/settings.json` |
| `commands/feature.md` | The orchestrator (`/feature`) |
| `commands/retro.md` | End-of-session retrospective → improvements document (`/retro`) |
| `commands/review-mrs.md` | Learns from GitLab merge requests via the GitLab MCP → improvements document (`/review-mrs`) |
| `agents/explorer.md` | Pattern and reusable-code discovery before planning (three run in parallel) |
| `agents/review-conventions.md` | Conventions reviewer (runs twice: code skills and test skills), filling in the checklists rule by rule |
| `agents/review-quality.md` | Duplication (exact and near), unused code, silenced linters, private members, changes the feature didn't need |
| `agents/review-spec.md`, `review-bugs.md`, `review-tests.md` | Spec coverage, bugs, and test quality |
| `agents/review-ui.md` | Walks the spec's journeys in the browser with the Playwright MCP server (only when you agreed in the grill) |
| `agents/review-test-plan.md` | One-pass review of `test-plan.md` before tests are written |
| `skills/python-conventions`, `pytest-conventions`, `vue-conventions` | House conventions (with `references/checklist.md` for reviewers) |
| `skills/sql-conventions` | Table models (indexes in `__table_args__`) and explicit transactions |
| `skills/vitest-conventions` | Frontend component tests (Vue Test Utils) and integration tests (real store/router + MSW) |
| `skills/browser-test-conventions` | Playwright browser tests with a fully mocked backend |
| `skills/backend-test-infra` | Integration vs API layers; Postgres, Mongo, proxy, RabbitMQ, Temporal test setup |
| `skills/git-worktree` | Creating, entering, setting up (including the branch's own Docker services), and removing a worktree |
| `workflow/grill-with-docs.md`, `write-spec.md`, `test-plan.md` | Phase guides that `/feature` reads (plain files, not skills) |
| `workflow/workflow-improvement.md` | Where an improvement belongs, the document template, how to apply changes safely (read by `/retro` and `/review-mrs`) |
| `workflow/templates/` | spec, plan, progress, and test-plan templates |
| `scripts/` | The checkers, the hook scripts, the mypy wrapper, the checklist skeleton, and their tests |

---

## Setup

1. **Requirements:** `python` (3.10+) on PATH for the hooks, and Docker for the test services. Per Python service: `uv`, plus `mypy`, `pytest-cov`, and `diff-cover` as dev dependencies. Frontend: ESLint, Vitest + Vue Test Utils + MSW + `@pinia/testing` already set up in the project. For the optional UI check in review, the Playwright MCP server connected to Claude Code.
2. **Install:** from this repo's `.claude/` folder, run `bash install.sh`. It copies `CLAUDE.md`, `agents/`, `commands/`, `skills/`, `workflow/`, and `scripts/` into `~/.claude/` (without caches), and adds the hooks to your existing `~/.claude/settings.json` without touching your other settings. It removes files the repo no longer has. Run it again after every `git pull`. If a file in `~/.claude` changed since the last install (for example through `/retro`), it lists the file and stops: copy the change into the repo's `.claude/` first, then run `bash install.sh --force`.
3. **Keep a root `CLAUDE.md` in each project** with the architecture, where things live, and the run/test commands. `/feature` reads it, and `/retro` recommends additions to it over time.

## LiteLLM

Point Claude Code at your LiteLLM proxy in the `env` block of `~/.claude/settings.json`. Every agent uses the session's model. Never commit the key.

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://<your-litellm-host>",
    "ANTHROPIC_AUTH_TOKEN": "<your LiteLLM key>",
    "ANTHROPIC_MODEL": "qwen3.8-27b"
  }
}
```

## What the hooks do

- **After every Write/Edit:** runs `scripts/lint_changed.py` on the edited file. For `.py` files that's the Python convention checker; for `.vue`/`.ts` files it's the Vue convention checker plus the project's `eslint` (when installed in `node_modules`). Only problems on lines the branch wrote are reported (a file that's new in the branch is checked whole). They're sent back to Claude (exit code 2) so it fixes them right away. Files outside the project (Claude's scratch scripts) are skipped. The rules and their IDs are in each skill's `references/checklist.md`; items marked `(auto)` are the ones the checkers enforce.
- **Before every Write/Edit to a test file:** while a feature is active (`docs/features/.active`), it blocks adding a pytest, Vitest, or Playwright test whose exact name isn't in that feature's `test-plan.md`. Edits to existing tests are allowed. Outside the workflow, the guard does nothing.
- **When Claude tries to end its turn (Stop):** while a feature is active and its spec is approved, it blocks stopping until `progress.md` says `Phase: DONE`. It allows stopping when `progress.md` has a `BLOCKED: <reason>` line, or after 3 blocks in a row with no progress (a loop guard).

## Using the scripts directly (e.g. in CI)

`--since auto` compares against the active feature's `Base:` commit, or the merge base with `origin/HEAD`. Leave it out to check whole files.

```bash
python ~/.claude/scripts/lint_changed.py --since auto <files>
```

```bash
python ~/.claude/scripts/check_python_conventions.py --since auto <files or dirs>
```

```bash
python ~/.claude/scripts/check_vue_conventions.py --since auto <files or dirs>
```

```bash
python ~/.claude/scripts/mypy_strict.py --since auto <paths>
```

## Testing the scripts

```bash
uv run --with pytest pytest ~/.claude/scripts/tests
```

## Improving the setup over time

- **`/retro [focus]`** at the end of a session: reviews the conversation, the feature artifacts in `docs/features/` of every worktree (including every review round in `review/round-<n>/` and `review/history.md`), and the diff, then writes `docs/improvements/<date>-session-<topic>.md`. Every recommendation has evidence, a destination (hook, convention skill + checklist, reviewer, workflow guide, `CLAUDE.md`, glossary/ADR, or a new skill/command), and the exact text to add. It then asks which `IMP-n` to apply and applies only those.
- **`/review-mrs <MR URL or group/project!iid> ...`**: the same, but the evidence is GitLab merge requests (human review comments, fix-up commits, the diff). It's **read-only on GitLab**. It needs a GitLab MCP server connected to Claude Code, with a token that has the `read_api` scope.

Both follow `workflow/workflow-improvement.md`.

## Parallel features (worktrees)

- Branches and worktree folders are named `BTRC-<JIRA-ISSUE>-<what-we-do>` (e.g. `BTRC-1234-add-authentication`), never `worktree-...`.
- `/feature` always works in its own worktree (pass `--no-worktree` to stay in the current checkout). It creates the worktree with git and enters it with `EnterWorktree` (`path`), because `EnterWorktree` with a name, and `claude -w`, would name the branch `worktree-<name>`.
- From a terminal: `git fetch origin`, then `git worktree add .claude/worktrees/<branch> -b <branch> origin/main`, then run `claude` inside `.claude/worktrees/<branch>`. To resume later, run `claude` there again, then `/feature resume <branch>`.
- **Tests use only the compose project named after the branch**, in lowercase (`docker compose -p btrc-1234-add-authentication`). When it isn't running, Claude creates it from the project's own `docker-compose.yml` with an override that frees the fixed ports, so tests never touch your containers or another branch's. See `skills/git-worktree/SKILL.md` §3.

## Model invocation

Which items are skills, plain workflow files, or commands, and why, is in `workflow/workflow-improvement.md` §6. `/retro` uses it for everything it proposes.
