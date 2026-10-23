# Test Plan

Write `docs/features/<slug>/test-plan.md` from `~/.claude/workflow/templates/test-plan.md`. **No test code is written before this file exists.** A hook blocks any new test whose name isn't in the plan.

## Inputs
- `spec.md` (REQ and EC IDs), `plan.md`, `progress.md` (deviations).
- The diff of the implementation: `git diff <base>` (the `Base:` SHA in `progress.md`, which includes uncommitted changes) plus untracked files.
- The reference test files from `patterns.md`.

## Rules
1. **One row per test function.** Parametrized tests are one row; list the cases in "What it tests".
2. **The test name column holds the exact name:**
   - pytest: the function name, `test_<unit>_<condition>_<expected>`.
   - Vitest: the exact `it(...)` string, e.g. `shows an error message when loading entities fails`.
   - Playwright: the exact `test(...)` string, e.g. `user creates an entity and sees it in the list`.
3. **The file path column holds the exact path** the test will live in, following `pytest-conventions` / `vitest-conventions` / `browser-test-conventions`. Put rows in the existing main file of their operation, component, or flow; plan a new file only for a new one.
4. **The expected result is observable:** a return value, status code plus body, raised exception plus message, DB state, emitted event, rendered text, URL. "Works correctly" isn't a result.
5. **Layers.** Use exactly these names in the Layer column:

   | Layer | Tool | Required for |
   |---|---|---|
   | `be-unit` | pytest | Pure backend helpers with no I/O |
   | `be-integration` | pytest | Every new/changed service manager/reader path, against a real test DB (`backend-test-infra`) |
   | `be-api` | pytest | Every new/changed endpoint, through the test client: success, each error status, response shape |
   | `fe-unit` | Vitest | **Shared** frontend utils, composables, stores, and the API client |
   | `fe-component` | Vitest + Vue Test Utils | Only **shared** components or components with important behavior: their contract (`vitest-conventions/references/component-tests.md`) |
   | `fe-integration` | Vitest + Vue Test Utils + MSW | The **important** flows of new or changed views: main flow, failures of important actions (`vitest-conventions/references/integration-tests.md`) |
   | `browser` | Playwright, mocked backend | Only when the user asked for browser tests in the grill: important user journeys (`browser-test-conventions`) |

   **Frontend rows are deliberately few** (see `vitest-conventions`, "What Gets a Frontend Test"): no rows for single-use presentational components, labels, styling, or every loading/empty/error state. Backend rows stay complete.

   Put edge-case depth in the cheapest layer that can prove it (`be-integration`, `fe-component`). Put "does it work together" in `fe-integration`. Keep `browser` to journeys.
6. **Coverage mapping:** every `REQ-n` and `EC-n` appears in "Covers" at least once. On the **backend**, every new public function, endpoint, consumer, workflow, and activity has at least one row, and every error branch in the diff has a row. Pure proxy pass-through routes are exempt (write them under "Exempt" with the reason). On the **frontend**, only shared code and important behavior get rows.
7. **Never plan these:** tests in `midnight_models`, tests of migrations, tests that only check which input a model or schema accepts (validation is tested through the API, e.g. a 422), and frontend tests outside the core scope.
8. Don't plan tests that only restate the implementation (e.g. "the mock was called") when a real result can be checked.

## Self-check
- [ ] Every REQ and EC is covered
- [ ] Every new endpoint has both `be-integration` and `be-api` rows
- [ ] Backend test files follow `tests/<domain>/test_<operation>_<domain>.py`, with manager and API rows of one operation in the same file
- [ ] No rows for migrations or plain schema/model validation
- [ ] Frontend rows cover only shared code and important behavior; important flows have `fe-integration` rows; `browser` rows exist only when the user asked for them
- [ ] Anything moved from jsdom to `browser` because jsdom can't handle it says so in "What it tests"
- [ ] Every row's expected result is concrete
- [ ] Names follow the naming conventions exactly

## After writing the tests
Run the tests on this branch's own services, and the backend changed-line coverage report (commands are in the root `CLAUDE.md`). The frontend has no coverage gate. Record the results at the bottom of `test-plan.md` under "Results". If a planned test turns out to be impossible or wrong, update its row with the reason instead of silently dropping it.
