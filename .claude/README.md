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
| `commands/map-services.md` | Generates `skills/service-map/` from the code (`/map-services`) |
| `agents/explorer.md` | Pattern discovery before planning |
| `agents/review-*.md` | The four reviewers |
| `skills/python-conventions`, `pytest-conventions`, `vue-conventions` | House conventions (with `references/checklist.md` for reviewers) |
| `skills/vitest-conventions` | Frontend component tests (Vue Test Utils) and integration tests (real store/router + MSW) |
| `skills/browser-test-conventions` | Playwright browser tests with a fully mocked backend |
| `skills/backend-test-infra` | Integration vs API layers; Postgres, Mongo, proxy, RabbitMQ, Temporal test setup |
| `skills/grill-with-docs`, `write-spec`, `test-plan` | Workflow phases (with templates) |
| `scripts/` | Hook scripts, the convention checker, the mypy wrapper, and their tests |

---

## Setup

1. **Requirements:** `python` (3.10+) on PATH for the hooks. Per Python service: `uv`, plus `ruff`, `mypy`, `pytest-cov`, and `diff-cover` as dev dependencies. Frontend: Vitest + Vue Test Utils + MSW + `@pinia/testing` (see `skills/vitest-conventions` §7) and Playwright (see `skills/browser-test-conventions` §7).
2. **Run from the project root:** `claude`. The first time, Claude Code asks you to trust the folder; the hooks in `settings.json` only run after you accept.
3. **Generate the service map** once: `/map-services`. Review the generated `.claude/skills/service-map/SKILL.md` and commit it.

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
