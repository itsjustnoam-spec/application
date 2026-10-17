---
name: test-plan
description: Use in the feature workflow after implementation and before writing any test. Produces test-plan.md, one row per test (test name, file path, what it tests, expected result), covering every requirement, edge case, and new code path. Tests may only be written once they are listed here.
disable-model-invocation: true
---

# Test Plan

Write `docs/features/<slug>/test-plan.md` from `templates/test-plan.md`. **No test code is written before this file exists.** A hook blocks any new test whose name isn't in the plan.

## Inputs
- `spec.md` (REQ and EC IDs), `plan.md`, `progress.md` (deviations).
- The diff of the implementation: `git diff <base>...HEAD` plus uncommitted changes.
- The reference test files from `patterns.md`.

## Rules
1. **One row per test function.** Parametrized tests are one row; list the cases in "What it tests".
2. **The test name column holds the exact name:**
   - pytest: the function name, `test_<unit>_<condition>_<expected>`.
   - Vitest: the exact `it(...)` string, e.g. `shows an error message when loading entities fails`.
   - Playwright: the exact `test(...)` string, e.g. `user creates an entity and sees it in the list`.
3. **The file path column holds the exact path** the test will live in, following `pytest-conventions` / `vitest-conventions` / `browser-test-conventions`.
4. **The expected result is observable:** a return value, status code plus body, raised exception plus message, DB state, emitted event, rendered text, URL. "Works correctly" isn't a result.
5. **Layers.** Use exactly these names in the Layer column:

   | Layer | Tool | Required for |
   |---|---|---|
   | `be-unit` | pytest | Pure backend helpers with no I/O |
   | `be-integration` | pytest | Every new/changed service manager/reader path, against a real test DB (`backend-test-infra`) |
   | `be-api` | pytest | Every new/changed endpoint, through the test client: success, each error status, response shape |
   | `fe-unit` | Vitest | Pure frontend utils/composables |
   | `fe-component` | Vitest + Vue Test Utils | Every new/changed component: props, slots, emits, and loading/error/empty states (`vitest-conventions/references/component-tests.md`) |
   | `fe-integration` | Vitest + Vue Test Utils + MSW | Every new/changed view or flow: real store + router, network mocked (`vitest-conventions/references/integration-tests.md`) |
   | `browser` | Playwright, mocked backend | Every new/changed user journey (happy path + journey-level failure), and behavior that is unreliable in jsdom (`browser-test-conventions`) |

   Put edge-case depth in the cheapest layer that can prove it (`be-integration`, `fe-component`). Put "does it work together" in `fe-integration`. Keep `browser` to journeys.
6. **Coverage mapping:** every `REQ-n` and `EC-n` appears in "Covers" at least once. Every new public function, endpoint, component, consumer, workflow, and activity has at least one row. Every error branch in the diff has a row. Pure proxy pass-through routes are exempt (write them under "Exempt" with the reason).
7. Don't plan tests that only restate the implementation (e.g. "the mock was called") when a real result can be checked.

## Self-check
- [ ] Every REQ and EC is covered
- [ ] Every new endpoint has both `be-integration` and `be-api` rows
- [ ] Every new component has `fe-component` rows for its props/emits and its loading, error, and empty states (when it has them)
- [ ] Every new or changed view/flow has `fe-integration` rows: main flow, each specified network failure, empty data
- [ ] Every new or changed user journey has a `browser` row (happy path), plus one for each journey-level failure in the spec
- [ ] Anything moved from jsdom to `browser` because jsdom can't handle it says so in "What it tests"
- [ ] Every row's expected result is concrete
- [ ] Names follow the naming conventions exactly

## After writing the tests
Run the tests and the coverage of changed lines (commands are in the root `CLAUDE.md`). Record the results at the bottom of `test-plan.md` under "Results". If a planned test turns out to be impossible or wrong, update its row with the reason instead of silently dropping it.
