# Claude Code workflow (project-level)

A spec-first Claude Code workflow for a Vue/Vuetify + FastAPI microservices monorepo. Everything lives in this `.claude/` folder, so running `claude` from the project root picks it up automatically. Nothing needs installing.

```
/feature "<what you want>"
  1 Explore & discover patterns → context.md, patterns.md
  2 Grill (batches of ≤4 questions, each with a recommendation) → grill-notes.md
  3 Spec + plan → ★ you approve (the only stop)
  4 Implement task by task (hooks check conventions after every edit)
  5 Test plan → test-plan.md   (a hook blocks tests that aren't in it)
  6 Write tests: backend, component, integration, browser + changed-line coverage
  7 Review in parallel: conventions · spec · bugs · tests
  8 Triage + fix (max 2 rounds)
  9 summary.md
```

Everything for a feature lives in `docs/features/<slug>/` (git-ignored). Resume an interrupted run with `/feature resume <slug>`.

---

## Layout

| Path | What |
|---|---|
| `settings.json` | Hooks: post-edit convention/lint check, test-plan guard |
| `commands/feature.md` | The orchestrator (`/feature`) |
| `commands/retro.md` | End-of-session retrospective → improvements document (`/retro`) |
| `commands/review-mrs.md` | Learns from GitLab merge requests via the GitLab MCP → improvements document (`/review-mrs`) |
| `agents/explorer.md` | Pattern discovery before planning |
| `agents/review-*.md` | The four reviewers |
| `skills/python-conventions`, `pytest-conventions`, `vue-conventions` | House conventions (with `references/checklist.md` for reviewers) |
| `skills/vitest-conventions` | Frontend component tests (Vue Test Utils) and integration tests (real store/router + MSW) |
| `skills/browser-test-conventions` | Playwright browser tests with a fully mocked backend |
| `skills/backend-test-infra` | Integration vs API layers; Postgres, Mongo, proxy, RabbitMQ, Temporal test setup |
| `skills/grill-with-docs`, `write-spec`, `test-plan` | Workflow phases (with templates) |
| `skills/workflow-improvement` | Where an improvement belongs, the document template, how to apply changes safely |
| `scripts/` | Hook scripts, the convention checker, the mypy wrapper, and their tests |

---

## Setup

1. **Requirements:** `python` (3.10+) on PATH for the hooks. Per Python service: `uv`, plus `ruff`, `mypy`, `pytest-cov`, and `diff-cover` as dev dependencies. Frontend: Vitest + Vue Test Utils + MSW + `@pinia/testing` (see `skills/vitest-conventions` §7) and Playwright (see `skills/browser-test-conventions` §7).
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
  - `.py`: runs `scripts/check_python_conventions.py` (page header, banners and spacing, `-> None`, `return None`, trailing `return`, untyped params, builtin exceptions, `Error` suffix, `__all__`, docstring layout, the multiline-call rule, BOM) plus `ruff check` when ruff is installed in the service's `.venv` or on PATH.
  - `.vue`/`.ts`: runs the project's `eslint` if one is installed in `node_modules`.
  - Problems are sent back to Claude (exit code 2) so it fixes them right away.
- **Before every Write/Edit to a test file:** while a feature is active (`docs/features/.active`), it blocks adding a pytest, Vitest, or Playwright test whose name isn't in that feature's `test-plan.md`. Edits to existing tests are allowed. Outside the workflow, the guard does nothing.

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

- **`/retro [focus]`** at the end of a session: reviews the conversation, the feature artifacts in `docs/features/`, and the diff, then writes `docs/improvements/<date>-session-<topic>.md`. Every recommendation has evidence, a destination (hook, convention skill + checklist, reviewer, workflow skill, `CLAUDE.md`, glossary/ADR, or a new skill/command), and the exact text to add. It then asks which `IMP-n` to apply and applies only those.
- **`/review-mrs <MR URL or group/project!iid> ...`**: the same, but the evidence is GitLab merge requests (human review comments, fix-up commits, the diff). It's **read-only on GitLab**. It needs a GitLab MCP server connected to Claude Code, with a token that has the `read_api` scope.

Both follow `skills/workflow-improvement/SKILL.md`.

## Model invocation

`disable-model-invocation: true` means Claude can't load the item on its own (its description isn't in context, and the Skill tool refuses it). You can still run it with `/name`, and commands read it by path.

| Item | Setting | Why |
|---|---|---|
| `python-conventions`, `pytest-conventions`, `vue-conventions`, `vitest-conventions`, `browser-test-conventions`, `backend-test-infra` | model-invoked | Claude must pick them up by itself whenever it writes that kind of code, inside or outside `/feature`, and the review agents load them |
| `grill-with-docs`, `write-spec`, `test-plan` | `true` | Phases of `/feature`. On their own they'd start a grill or create workflow files in the middle of unrelated work. `/feature` reads them by path |
| `workflow-improvement` | `true` | Only meaningful inside `/retro` and `/review-mrs`, which read it by path |
| `/feature`, `/retro`, `/review-mrs` | `true` | Long-running and write files, so you start them on purpose |

When you add a skill, decide with the policy in `skills/workflow-improvement/SKILL.md` §6. `/retro` does this for the skills it proposes.
