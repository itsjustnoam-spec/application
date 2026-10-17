# Claude Code workflow (project-level)

A spec-first Claude Code workflow for a Vue/Vuetify + FastAPI microservices monorepo. Everything lives in this `.claude/` folder, so running `claude` from the project root picks it up automatically. Nothing needs installing.

```
/feature "<what you want>"
  1 Explore & discover patterns → context.md, patterns.md
  2 Grill (batches of ≤4 questions, each with a recommendation) → grill-notes.md
  3 Spec + plan → ★ you approve (the only stop)
  4 Implement task by task (hooks check conventions after every edit)
  5 Test plan → test-plan.md, reviewed once by review-test-plan (a hook blocks tests that aren't in it)
  6 Write tests: backend, component, integration, browser + changed-line coverage
  7 Review in parallel: conventions · spec · bugs · tests
  8 Triage + fix (max 3 rounds; every round kept in review/round-<n>/)
  9 summary.md
```

Everything for a feature lives in `docs/features/<slug>/` (git-ignored). Resume an interrupted run with `/feature resume <slug>`.

---

## Layout

| Path | What |
|---|---|
| `settings.json` | Hooks: post-edit convention/lint check, test-plan guard, and a Stop hook that keeps a run going until `Phase: DONE` |
| `commands/feature.md` | The orchestrator (`/feature`) |
| `commands/retro.md` | End-of-session retrospective → improvements document (`/retro`) |
| `commands/review-mrs.md` | Learns from GitLab merge requests via the GitLab MCP → improvements document (`/review-mrs`) |
| `agents/explorer.md` | Pattern discovery before planning |
| `agents/review-*.md` | The four reviewers |
| `skills/python-conventions`, `pytest-conventions`, `vue-conventions` | House conventions (with `references/checklist.md` for reviewers) |
| `skills/vitest-conventions` | Frontend component tests (Vue Test Utils) and integration tests (real store/router + MSW) |
| `skills/browser-test-conventions` | Playwright browser tests with a fully mocked backend |
| `skills/sql-conventions` | Explicit transactions, rolled back with `transaction.rollback()` (never `session.rollback()`) |
| `agents/review-test-plan.md` | One-pass review of `test-plan.md` before tests are written |
| `skills/backend-test-infra` | Integration vs API layers; Postgres, Mongo, proxy, RabbitMQ, Temporal test setup |
| `skills/git-worktree` | Creating, entering, setting up, and removing a worktree per feature, for parallel work |
| `workflow/grill-with-docs.md`, `write-spec.md`, `test-plan.md` | Phase guides that `/feature` reads (plain files, not skills) |
| `workflow/workflow-improvement.md` | Where an improvement belongs, the document template, how to apply changes safely (read by `/retro` and `/review-mrs`) |
| `workflow/templates/` | spec, plan, progress, and test-plan templates |
| `scripts/` | Hook scripts, the convention checker, the mypy wrapper, and their tests |

---

## Setup

1. **Requirements:** `python` (3.10+) on PATH for the hooks. Per Python service: `uv`, plus `ruff`, `mypy`, `pytest-cov`, and `diff-cover` as dev dependencies. Frontend: ESLint, Vitest + Vue Test Utils + MSW + `@pinia/testing`, and Playwright, already set up in the project.
2. **Run from the project root:** `claude`. The first time, Claude Code asks you to trust the folder; the hooks in `settings.json` only run after you accept.
3. **Keep a root `CLAUDE.md`** with the architecture, where things live, and the run/test commands. `/feature` reads it, and `/retro` recommends additions to it over time.

## LiteLLM models

The agents ask for `sonnet` (explorer, review-spec, review-bugs, review-tests) or `haiku` (review-conventions). Map those aliases to your LiteLLM models in your **user** settings (`~/.claude/settings.json`), or in `.claude/settings.local.json` (git-ignored by Claude Code), never in the shared `settings.json`, because the key is personal. The model names below are placeholders; use the `model_name`s from your LiteLLM config:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://<your-litellm-host>",
    "ANTHROPIC_AUTH_TOKEN": "<your LiteLLM key>",
    "ANTHROPIC_MODEL": "qwen3.8-27b",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "qwen3.8-27b",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "qwen3.8-27b",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-5.3-flash"
  }
}
```

## What the hooks do

- **After every Write/Edit**
  - `.py`: runs `scripts/check_python_conventions.py` (page header, banners and spacing, `-> None`, `return None`, trailing `return`, untyped params, builtin exceptions, `Error` suffix, `__all__`, docstring layout, no blank line after a class docstring, `__tablename__` first and `__table_args__` last in table models, a blank line after `if` blocks, the 70-character multiline-call rule, a docstring on every function, no short or abbreviated names, no dependencies stored in constants, multi-line comprehensions, `pass` in empty classes, no `session.rollback()`, imperative-mood descriptions, `Whether ...` boolean returns, `StrEnum` for string enums, one item per line in list and set literals, BOM; in test files: no page docstring or banners, no `session.add/commit/...`, and no object creation outside the `env` fixture; migration files are skipped) plus `ruff check` when ruff is installed in the service's `.venv` or on PATH. Files outside the project (Claude's scratch scripts) are skipped.
  - `.vue`/`.ts`: runs the project's `eslint` if one is installed in `node_modules`.
  - Problems are sent back to Claude (exit code 2) so it fixes them right away.
- **Before every Write/Edit to a test file:** while a feature is active (`docs/features/.active`), it blocks adding a pytest, Vitest, or Playwright test whose name isn't in that feature's `test-plan.md`. Edits to existing tests are allowed. Outside the workflow, the guard does nothing.
- **When Claude tries to end its turn (Stop):** while a feature is active and its spec is approved, it blocks stopping until `progress.md` says `Phase: DONE`, and tells Claude which step comes next. It allows stopping when `progress.md` has a `BLOCKED: <reason>` line, or after 3 blocks in a row with no progress (a loop guard).

## Using the scripts directly (e.g. in CI)

```bash
python .claude/scripts/check_python_conventions.py <files or dirs>
```

```bash
python .claude/scripts/mypy_strict.py <paths>
```

## Testing the scripts

```bash
uv run --with pytest pytest .claude/scripts/tests
```

## Improving the setup over time

- **`/retro [focus]`** at the end of a session: reviews the conversation, the feature artifacts in `docs/features/` of every worktree (including every review round in `review/round-<n>/` and `review/history.md`), and the diff, then writes `docs/improvements/<date>-session-<topic>.md`. Every recommendation has evidence, a destination (hook, convention skill + checklist, reviewer, workflow guide, `CLAUDE.md`, glossary/ADR, or a new skill/command), and the exact text to add. It then asks which `IMP-n` to apply and applies only those.
- **`/review-mrs <MR URL or group/project!iid> ...`**: the same, but the evidence is GitLab merge requests (human review comments, fix-up commits, the diff). It's **read-only on GitLab**. It needs a GitLab MCP server connected to Claude Code, with a token that has the `read_api` scope.

Both follow `workflow/workflow-improvement.md`.

## Parallel features (worktrees)

- From a terminal: `claude -w <slug>`, then `/feature ...` inside it. To resume later: `claude -w <slug>`, then `/feature resume <slug>`.
- From a session: `/feature --worktree <description>`. `/feature` also moves into a worktree automatically when another feature is already active in the checkout, and otherwise asks once.
- Worktrees live in `.claude/worktrees/<slug>/` (gitignored) on branch `worktree-<slug>`, pushed as `feature/<slug>`. Each one has its own `docs/features/`. See `skills/git-worktree/SKILL.md` for setup (dependencies, `.worktreeinclude` for `.env` files, shared Docker infrastructure) and cleanup.
- New worktrees branch from `main` on the remote, so **commit and push changes to `.claude/` to `main`** before starting worktrees. Otherwise they run the old workflow.

## Model invocation

`disable-model-invocation: true` means Claude can't load the item on its own: its description isn't in context, and Claude Code **refuses a Skill tool call to it** and tells Claude not to do the steps another way. That's why nothing the workflow depends on may carry the flag.

| Item | Form / setting | Why |
|---|---|---|
| `python-conventions`, `pytest-conventions`, `sql-conventions`, `vue-conventions`, `vitest-conventions`, `browser-test-conventions`, `backend-test-infra` | Skill, model-invoked | Claude must pick them up by itself whenever it writes that kind of code, inside or outside `/feature`, and the review agents load them |
| `git-worktree` | Skill, model-invoked | Claude should reach for it when you start parallel work; `/feature` loads it in phase 0 |
| `grill-with-docs`, `write-spec`, `test-plan`, `workflow-improvement` | **Plain files in `workflow/`**, not skills | Only meaningful inside their command. As flagged skills they got refused mid-workflow and stopped `/feature` at phase 5. As plain files they can't misfire on their own and can't be blocked |
| `/feature`, `/retro`, `/review-mrs` | Command, `true` | Long-running and write files, so you start them on purpose |

When you add something, decide its form with `workflow/workflow-improvement.md` §6. `/retro` does this for everything it proposes.
