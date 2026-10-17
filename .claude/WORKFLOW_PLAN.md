# Coding Workflow: Starting Plan

> **Note:** this plan was written when the workflow was a plugin. It now lives in `.claude/` as project-level config. See `.claude/README.md`; commands are `/feature`, `/retro`, and `/review-mrs`. The service map was dropped in favor of the root `CLAUDE.md`. Phase guides now live in `.claude/workflow/`, the fix loop is up to 3 rounds, and features can run in parallel worktrees (`skills/git-worktree`).

> **Status (16/10/26):** Build steps 1–7 are implemented as the `noam-workflow` plugin in this folder. See `README.md` for install and usage. Still open: generating the real service map in the monorepo (`/noam-workflow:map-services`), the first live run on your LiteLLM models, and the model benchmark (§5). The service map now lives in the monorepo (`.claude/skills/service-map/`), not in the plugin.

A spec-first Claude Code workflow for a Vue/Vuetify frontend and FastAPI microservices (reverse proxy, CRUD on Postgres, Mongo service, Temporal, RabbitMQ). It runs on LiteLLM with **GLM-5.3-Flash** and **Qwen3.8-27B**.

Working name: **`/feature`**. It's one command that runs every phase, with **one human gate**: approving the spec and plan.

---

## 0. Design principles (and why they matter for these models)

GLM-Flash and a 27B Qwen are capable, but they're weaker than frontier models at long, unstructured, self-directed work. The workflow is built around that:

1. **Everything lives on disk as artifacts.** Each phase writes a file (`spec.md`, `plan.md`, `progress.md`, `test-plan.md`, `review/*.md`). Later phases read the files, not the chat history. This survives context compaction and keeps each subagent's context small.
2. **IDs give traceability.** Requirements are `REQ-n`, edge cases are `EC-n`, tests are `T-n`, findings are `F-n`. Reviewers check those IDs mechanically instead of judging "does this feel right".
3. **Deterministic checks come before LLM judgment.** Anything a script can verify (formatting, `-> None`, section banners, coverage on changed lines, types) is checked by a script. Reviewers spend their tokens on what scripts can't catch.
4. **Instructions are short and checklist-shaped.** Every skill stays under ~200 lines, with detail moved into `references/`. Each reviewer has one job and a fixed output format.
5. **Ambiguity is resolved before the gate, not after.** After approval the agent never asks; anything uncertain must already be in the spec as a decision.

---

## 1. The phases

```
 /feature "<description>"
   │
   ├─ 1. Explore      (subagent, read-only)        → context.md
   ├─ 2. Grill        (interactive, with the user) → decisions logged into spec.md
   ├─ 3. Spec + Plan  (writer)                     → spec.md, plan.md
   │
   ├─ ★ GATE: you approve spec.md + plan.md  ← the only stop
   │
   ├─ 4. Implement    (task by task)             → code, progress.md
   ├─ 5. Test plan    (writer)                   → test-plan.md
   ├─ 6. Write tests  (writer)                   → tests, coverage report
   ├─ 7. Review       (4 parallel subagents)     → review/*.md
   ├─ 8. Fix loop     (triage → fix → re-review, max 2 rounds)
   └─ 9. Summary                                 → summary.md
```

Artifacts go in `docs/features/<slug>/`, which is **git-ignored**. The plugin, the root `CLAUDE.md`, and the `service-map` skill all live at the monorepo root, so one `/feature` run can touch several services.

### Phase 1: Explore and discover patterns (read-only subagent, mandatory)
The workflow never plans before this phase is done. The spec phase refuses to start if `patterns.md` is missing.
- Inputs: the feature description, `CLAUDE.md`, and the `service-map` skill.
- It finds the touched services, the relevant models and schemas, proxy routes, queues, Temporal workflows, and Vue components and stores.
- **Pattern discovery:** for each kind of change the feature needs (new endpoint, new SQLModel entity + service manager/reader, Mongo repository, proxy route, RabbitMQ consumer/publisher, Temporal workflow/activity, Vue view/dialog/store, API client call, tests), it finds **1–2 existing examples in the monorepo** and records how they're done there.
- Outputs:
  - `context.md`: files and their roles, and the integration points between services.
  - `patterns.md`: one entry per pattern, with **the name · reference file(s) · the shape to copy** (layers, naming, error handling, how it's wired and registered, how it's tested). It also lists **inconsistencies**, where the codebase does the same thing two ways. Those become grill questions ("follow A or B?").
- Rule from Matt Pocock's approach: **the agent must never ask you something the code can answer.** That's why this phase runs before the grill.

### Phase 2: Grill with docs (interactive)
Adapted from `grill-me` / grill-with-docs, with changes for upfront precision:
- Questions are asked in **batches of up to 4 related questions** (`AskUserQuestion`). That's faster than one at a time but still focused. **Every question includes a recommended answer and a one-line reason**, so you can usually just accept it.
- The agent works through a fixed **coverage checklist** so nothing gets skipped:
  behavior and user flows · data model and migrations · API contract (request/response, status codes) · proxy routing · auth and permissions · errors and failure modes · edge cases · cross-service effects (RabbitMQ messages, Temporal workflows, idempotency, retries) · UI states (loading/empty/error) · non-goals · backward compatibility · **which pattern from `patterns.md` to follow wherever there's a choice or an inconsistency** · **git strategy for this feature** (branch name, commit per task or one commit at the end, open a PR or not).
- It keeps an **Unknowns ledger**: every assumption it's making gets listed. Each one has to become a confirmed decision or another question. The grill ends only when the ledger is empty.
- It ends with a **readback**: about 5 bullets saying "here's what I'll build". You confirm or correct.
- Like Matt's version, it updates the domain glossary and decision log (`docs/CONTEXT.md` / ADRs) with any new terms or decisions, so the next feature starts smarter.

### Phase 3: Spec + Plan
`spec.md` (template-driven):
- Goal and non-goals
- `REQ-n` requirements, each with acceptance criteria
- API contracts per service (endpoint, payload, response, errors), the proxy route, and TS types that mirror the Pydantic models
- Data changes (SQLModel models plus the migration; Mongo document shape and indexes)
- Async: RabbitMQ message schemas and Temporal workflows/activities (timeouts, retries, idempotency)
- Frontend: components, states, and stores
- `EC-n` edge cases
- Decisions (from the grill)
- **Open questions: must be empty before the gate**

- Git strategy (from the grill)

`plan.md`: ordered tasks grouped by service. Each task lists its files, the `REQ` IDs it covers, **the pattern it follows (a `patterns.md` entry plus a reference file)**, and how to verify it (the command to run). Dependency order is backend model → service manager → API route → proxy route → frontend. A task that doesn't follow any existing pattern must say so and explain why, so you see it at the gate.

**★ Gate:** you approve both files, or comment and the agent revises. After this point, no more questions.

### Phase 4: Implement (autonomous)
- Works task by task from `plan.md` and ticks boxes in `progress.md`, so it can resume after compaction or a crash.
- Before each task it opens that task's reference file from `patterns.md` and mirrors its structure.
- Git follows the strategy you approved in the spec: branch, commits, and PR.
- After each task: `ruff`, the mypy wrapper, `eslint`/`vue-tsc` on the touched files, and the existing tests for that service (regressions only; new tests come later).
- If it hits something the spec doesn't cover, it doesn't ask. It picks the most conservative option, logs it in `progress.md → Deviations`, and the summary surfaces it.
- No TDD, as you asked.

### Phase 5: Test plan (written before any test code)
`test-plan.md`, one row per test, using your format plus two traceability columns:

| ID | Test name | File path | What it tests | Expected result | Covers |
|----|-----------|-----------|---------------|-----------------|--------|
| T-1 | `test_create_entity_duplicate_name_raises_duplicate_entity_error` | `tests/entities/test_create_entity.py` | Creating an entity whose name already exists | Raises `DuplicateEntityError`, no row inserted | REQ-2, EC-1 |

Rules: every `REQ` and every `EC` must appear in "Covers" at least once, and every new public function or endpoint needs at least one row. Pure proxy pass-through routes are exempt, per your pytest conventions.

The plan has an extra **Layer** column, and backend features need both layers:
- **Integration**: calls the service manager/reader directly (e.g. the entities reader) against a real test database, so business logic and ORM behavior are tested without HTTP.
- **API**: calls the endpoint through the FastAPI test client, so routing, validation, status codes, and response shapes are tested end to end within the service.

A typical new endpoint gets integration rows for its logic and edge cases, plus API rows for success, validation errors, and error-to-status mapping. Frontend rows use the **Vitest** layer.
Optional: a hook can **block writing to `tests/`** until `test-plan.md` exists, which enforces "plan first" mechanically.

### Phase 6: Write tests
- Follows `pytest-conventions` and the new `vitest-conventions`.
- Runs the tests, then **`diff-cover`**, which reports coverage *only on the lines this branch changed* (`--fail-under=100`). That's how "100% of new code" becomes a hard number instead of an estimate.

### Phase 7: Review (4 parallel read-only subagents)
Each reviewer gets only the diff, the artifacts, and its own skill. They all share one output format:
`| F-n | severity (blocker/major/minor) | file:line | rule / REQ / EC | finding | suggested fix |`

| Agent | Job | How it stays precise |
|---|---|---|
| **review-conventions** | Conventions in changed files | Uses the prebuilt checklist in each skill's `references/checklist.md` instead of re-deriving it. Outputs ✅/❌ per item per file. The deterministic script handles formatting rules, so this agent focuses on judgment rules such as naming, docstring content, component size, and theme usage. It also checks **pattern adherence**: each changed file is compared with its reference file from `patterns.md`. |
| **review-spec** | Code matches the spec | Builds a traceability matrix: each `REQ` maps to where it's implemented and whether it's done, partial, or missing. It also flags anything **built that isn't in the spec** (scope creep) and every `Deviation`. |
| **review-bugs** | Bugs and edge cases | Its checklist targets your stack: async/await mistakes, SQLAlchemy session and transaction handling, N+1 queries, Mongo query injection and missing indexes, Temporal determinism (no `datetime.now`/random/IO inside workflows), activity idempotency, RabbitMQ ack/requeue and poison messages, proxy path and header forwarding, mismatches between Pydantic and TS types, and Vue reactivity pitfalls. It walks every `EC` and checks how the code handles it. |
| **review-tests** | Test quality | Checks: (1) every `test-plan.md` row exists with a matching name and path; (2) the `diff-cover` result; (3) every `EC` has a test, and every new endpoint has **both integration and API tests**; (4) **every test asserts something meaningful**, flagging no-assert tests, `assert True`, tests that assert only on mocks, and duplicate tests; (5) pytest/vitest conventions. |

Model note: reviewers tend to report false positives, especially smaller models. That's why phase 8 starts with triage.

### Phase 8: Fix loop
1. The orchestrator **triages** each finding: *fix* or *dismiss with a reason*. It verifies a finding against the code before acting on it.
2. It fixes, re-runs the deterministic checks, and then **re-runs only the reviewers that had findings**.
3. There are at most 2 rounds. Anything still open goes into the summary instead of looping forever.

### Phase 9: Summary
`summary.md`: what was built (by REQ), deviations, dismissed findings with reasons, coverage numbers, and anything left open.

---

## 2. Skills and agents to create

```
noam-workflow/                      ← a Claude Code plugin (shareable with the team) or ~/.claude
  .claude-plugin/plugin.json
  commands/feature.md               ← orchestrator: runs phases, enforces the gate
  skills/
    python-conventions/             ← EXISTING (light fixes, see §3) + references/checklist.md
    pytest-conventions/             ← EXISTING (light fixes, see §3) + references/checklist.md
    vue-conventions/                ← EXISTING (light fixes, see §3) + references/checklist.md
    vitest-conventions/             ← NEW: frontend tests (Vitest + Vue Test Utils + Vuetify)
    service-map/                    ← NEW: architecture and how services talk (see below)
    grill-with-docs/                ← NEW: phase 2 rules, coverage checklist, unknowns ledger
    write-spec/                     ← NEW: spec.md + plan.md templates and quality bar
    test-plan/                      ← NEW: test-plan.md format and coverage rules
    backend-test-infra/             ← NEW: how to test Postgres / Mongo / Temporal / RabbitMQ
  agents/
    explorer.md                     ← read-only, cheap model
    review-conventions.md
    review-spec.md
    review-bugs.md
    review-tests.md
  hooks/hooks.json                  ← format/lint on edit; optional tests/ guard
  scripts/
    check_python_conventions.py     ← AST/regex checker (see §4)
    mypy_strict.sh                  ← mypy wrapper (see §4)
  templates/ spec.md · plan.md · test-plan.md · review.md · summary.md
```

**About the new skills:**
- **`service-map`** is probably the most valuable new skill. It describes each service's responsibility, how to add a route to the reverse proxy, how services call each other, the RabbitMQ exchanges/queues and message conventions, Temporal task queues and workflow conventions, and how to run and test each service. **I'd generate the first draft by having the agent scan your repos**, then you correct it.
- **`backend-test-infra`** is kept separate from `pytest-conventions` so the existing skill isn't touched. It defines the **two backend test layers**: integration tests through the service manager/reader, and API tests through the FastAPI test client, each with its own fixtures, a reference test file, and when to use which. It also covers what the general skill doesn't: a real Postgres for the CRUD service (testcontainers, or your existing setup; the SQLite example in pytest-conventions can hide Postgres-specific behavior), `mongomock`/a test Mongo for the other service, `temporalio.testing.WorkflowEnvironment` for workflows, and mocking at the RabbitMQ publisher boundary.
- Optional, later: per-stack skills like `fastapi-conventions`, `sqlmodel-conventions`, and `temporal-conventions`, if your team has conventions there that aren't written down yet. The grill/explore phases will show where they're needed.

---

## 3. Changes to your 3 convention files (core kept intact)

Nothing below changes a rule. These are fixes, clarifications, and additions.

**python-conventions**
- 🔴 **The file starts with a UTF-8 BOM** (`EF BB BF`). That can stop the `---` frontmatter from being recognized, so the skill may silently never load. Re-save it as UTF-8 without a BOM.
- 🔴 **There's garbled text** on lines 32, 78, and 114 (`- €”`, `- ’ - ‚¬ - €`). These were em-dashes; replace them.
- The code examples are indented with 1 space. Use 4 so the examples are valid Python, since models copy what they see.
- It references a **`uv` skill that isn't among your files**. Either add a tiny `uv` skill or inline the 3–4 uv rules.
- §8 says `tests/MODULE/what_we_test.py`, but pytest-conventions says `test_<what_we_test>.py`. Align them to the latter.
- The path reference `skills/pytest-conventions/SKILL.md` should just name the skill.
- **Clarify the `return` rule** (your answer to Q6): no trailing `return` is needed at the end of a function. A bare `return` is only for early exits, and `return None` is never written. Remove the trailing `return` from the GOOD example so models don't copy it.
- Add `references/checklist.md`: the rules rewritten as one-line yes/no checks, for the conventions reviewer.

**pytest-conventions**
- "One assertion concept per test" conflicts with the fixture-factory example, which asserts admin *and* member. Split the example into two tests (or parametrize it) so the example matches the rule.
- Add one line pointing to `backend-test-infra` for the integration and API layers and for DB, Temporal, and queue setups.
- Add a `references/checklist.md`.

**vue-conventions**
- The description mentions Tailwind. Keep it if you use it; you didn't list it in your stack.
- Add a "Testing" pointer to `vitest-conventions`. Right now **the frontend has no test conventions at all**. Vitest isn't set up in the project yet, so the skill also includes setup notes (Vitest + Vue Test Utils + Vuetify + coverage). The frontend gets the same ~100% new-code target.
- Mirror the Python `return` clarification for TypeScript: no trailing `return` in functions that return nothing, and `return` only for early exits.
- Add a `references/checklist.md`.

**Renames:** the current names are fine. Optionally prefix them (`conv-python`, `conv-pytest`, `conv-vue`) so they group together.

---

## 4. Deterministic tooling (takes load off the models)

| Check | Tool |
|---|---|
| Formatting / lint | `ruff format` + `ruff check`; `eslint` + `prettier`; `vue-tsc` |
| Types (respecting the no-`-> None` rule) | `mypy_strict.sh`: runs `mypy --strict` and filters **only** the message `Function is missing a return type annotation`. Missing *parameter* annotations have a different message and still fail. This turns your "ignore that mypy error" rule into an automated check. |
| House rules a linter can't express | `check_python_conventions.py` (AST): module docstring with `:author:`/`:date:`, banner format and exact blank lines, `-> None` forbidden, `return None` forbidden, raising builtin exceptions forbidden, exception names end in `Error`, no `__all__`, multiline-call rule (3+ args or 50+ chars) |
| Coverage on new code | `pytest --cov` / `vitest --coverage` → `diff-cover --fail-under=100` |

⚠️ **Formatter conflict to know about:** `ruff format`/black collapses calls that fit in 88 chars onto one line, which contradicts your 50-char multiline rule. It works *if* the code has a trailing comma (the "magic trailing comma" keeps the call expanded), so the checker should enforce trailing commas on calls that qualify.

Hooks: a `PostToolUse` hook on Edit/Write runs the formatter and the convention checker on the edited file and feeds errors straight back to the model.

---

## 5. Model setup through LiteLLM

- Point Claude Code at LiteLLM (`ANTHROPIC_BASE_URL`, auth token), then map the aliases: `ANTHROPIC_DEFAULT_SONNET_MODEL` / `ANTHROPIC_DEFAULT_OPUS_MODEL` → the stronger model, and `ANTHROPIC_DEFAULT_HAIKU_MODEL` → the faster one. Agents then just declare `model: sonnet` or `model: haiku` in frontmatter, and you can swap the real models in one place.
- Starting assignment (to validate, not assume):
  - Stronger model: grill, spec/plan, implementation, review-bugs, review-spec, triage
  - Faster model: explorer, review-conventions (checklist-driven), review-tests' mechanical checks
- **Benchmark it:** run the workflow on 2–3 past tickets you already know the answer to, once with each assignment. Compare spec quality, how many bugs review-bugs catches, and the false-positive rate. I don't have reliable data on how these two specific models compare, so measure it rather than guess.
- Check that tool calling through LiteLLM is solid for both models, especially parallel subagents and `AskUserQuestion`. That's the most common failure point with non-Anthropic models in Claude Code.

---

## 6. Build order

1. **Fix the conventions**: the §3 fixes plus the 3 checklists. Small and immediately useful.
2. **Deterministic layer**: `mypy_strict.sh`, `check_python_conventions.py`, diff-cover, hooks.
3. **`service-map`**: generated from your repos, then corrected by you.
4. **Front half**: `explorer` + `grill-with-docs` + `write-spec` + templates. Trial the grill on one real feature.
5. **Back half**: implement loop + `test-plan` + `vitest-conventions` + `backend-test-infra`.
6. **Reviewers + fix loop.**
7. **`/feature` orchestrator** to stitch it together, then the benchmark from §5 and tuning.

---

## 7. Decisions (answered 2026-10-16)

| # | Topic | Decision |
|---|---|---|
| 1 | Repo layout | Monorepo. The plugin, `CLAUDE.md`, and `service-map` live at the root, and one run can span services. |
| 2 | Frontend tests | Vitest isn't set up yet but will be. `vitest-conventions` is in scope (including setup notes), with the same ~100% new-code target. |
| 3 | Feature artifacts | `docs/features/<slug>/` is git-ignored. |
| 4 | Git automation | Decided per feature during the grill. The approved spec records the branch, commit, and PR strategy. |
| 5 | Backend test layers | Both layers are required: **integration** tests through the service manager/reader (e.g. entities) and **API** tests through the test client. |
| 6 | `return` rule | No trailing `return` is needed. A bare `return` is only for early exits, and `return None` is never written. This applies to Python and TS. |
| 7 | Grill pace | Batches of up to 4 questions. |
| + | Patterns | Pattern discovery (`patterns.md`) is a mandatory gate before planning. Every plan task names the pattern and reference file it follows, and the reviewers check adherence. |
