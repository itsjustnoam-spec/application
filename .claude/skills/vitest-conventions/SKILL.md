---
name: vitest-conventions
description: Use when writing, reviewing, or setting up frontend tests with Vitest for Vue 3 + Vuetify + TypeScript, covering both component tests (Vue Test Utils) and frontend integration tests (a whole view with real store, router, and MSW-mocked network). Defines what to test (only shared code and important behavior), layers, file layout, naming, AAA structure, and mocking boundaries.
---

# Vitest Frontend Testing Conventions

The frontend counterpart of `pytest-conventions`. It covers two Vitest layers:

| Layer | What is mounted | What is mocked | Detailed rules |
|---|---|---|---|
| **fe-component** | One component, with its real children | API client module (`vi.mock`), store actions (`createTestingPinia`) | `references/component-tests.md` |
| **fe-integration** | A whole view or feature, with real children, real Pinia, real router, real API client | **Only the network**, through MSW | `references/integration-tests.md` |
| fe-unit | Pure utils/composables without DOM | Nothing (or the clock) | this file only |

Browser tests (real browser, mocked backend) are a separate layer. See `browser-test-conventions`.

## What Gets a Frontend Test (and What Doesn't)

Frontend code changes often, and small UI changes shouldn't break a pile of tests. So frontend tests cover **only core behavior**:

- **Shared code**: anything used by more than one component, such as utils, composables, stores, the API client, and shared components. A bug there spreads, so it gets tested.
- **Important behavior**: the feature's main user flow, and behavior where a bug really hurts, such as losing or corrupting data, destructive actions (delete, archive), permissions, and money.

**Don't test:**
- A component used in only one place, beyond what its flow's integration test already exercises.
- How props map to rendered output, texts and labels, styling and layout, or every loading, empty, and error state of every page.
- Simple form wiring (a field bound to a model) or Vuetify behavior itself.

There's **no coverage target** for frontend code. Coverage of new frontend code isn't measured as a gate.

**Read the reference file for the layer you are writing before you write it.** Test code also follows `vue-conventions` (explicit checks, named constants, descriptive names). Reviewers use `references/checklist.md`.

---

## 1. Core Principles (all layers)

1. **Test behavior through the public interface:** props, emitted events, slots, rendered output, and user interaction. Never assert internal refs, call component methods, or reach into `wrapper.vm`. Logic that needs deep testing goes into a util with its own fe-unit test.
2. **Arrange-Act-Assert, visibly:** separate the three blocks with single blank lines. No `// Arrange` comments, and no comments in tests unless they document a non-obvious workaround.
3. **One behavior per test:** multiple `expect`s only when they check the same outcome.
4. **No loops or conditionals in tests:** use `it.each` for variations.
5. **DAMP over DRY:** a test reads top to bottom. Factories and mount helpers are fine; hiding the arrange step behind clever abstractions isn't.
6. **Mock at the boundary you own:** the API client (component layer) or the network (integration layer), plus timers and browser APIs. Never mock the unit under test. Don't stub child components by default.
7. **Isolation:** a fresh Pinia per test, a fresh router per test, mocks restored after each test (`restoreMocks: true` in config), and MSW handlers reset after each test. Tests pass in any order.
8. **Interact like a user:** `await wrapper.get(...).trigger('click')` and `await input.setValue(...)`. Always `await` them, because Vue updates the DOM asynchronously.
9. **Wait for real things:** `await flushPromises()` after anything that triggers network work. Never use `setTimeout`/sleep waits.
10. **No snapshot-only tests:** a snapshot never replaces asserting the behavior.

---

## 2. Files & Layout

```
tests/
  unit/<mirror of src path>/<Name>.spec.ts            # fe-component and fe-unit
  integration/<feature>/<flow>.spec.ts                # fe-integration
  e2e/...                                             # browser (see browser-test-conventions)
  mocks/
    factories/<entity>.ts      # typed test-data factories (shared by every layer)
    handlers/<domain>.ts       # MSW happy-path handlers per backend domain
    handlers/index.ts          # combines all handlers
    server.ts                  # setupServer(...handlers)
  utils/
    mount.ts                   # mountWithPlugins (Vuetify + router + pinia options)
  setup.ts                     # Vitest setup file (MSW lifecycle, ResizeObserver)
```

*If the project already has a different layout when Vitest is set up, follow that one and update this section.*

Internal file order (as in pytest-conventions): imports, then module-level mocks (`vi.mock`, which is hoisted anyway), then local helpers/constants, then one `describe('<UnitName>')` containing the tests.

---

## 3. Naming

- `describe('<ComponentName>')` for component tests, `describe('<Feature>: <flow>')` for integration tests.
- `it('<expected behavior> when <condition>')`, as a plain sentence about observable behavior:
  - `it('shows an error message when loading entities fails')`
  - `it('emits update with the entity id when the save button is clicked')`
  - `it('lists the created entity after the create dialog is submitted')`
- The `it(...)` string must match the "Test name" column of `test-plan.md` exactly. A hook enforces this.

---

## 4. Test Data

- Build every object through a typed factory from `tests/mocks/factories/`: `makeEntity({ name: 'Pump' })`. Factories return the **API types from `src/models/`**, so a contract change breaks the factories at compile time.
- Defaults are valid and realistic. Each test overrides only the fields that matter to it, so the arrange step shows what the test is about.
- The same factories feed MSW handlers, `vi.mock` return values, and Playwright fixtures.

---

## 5. Selectors

Vue Test Utils has no accessibility queries, so:
- Select elements by `data-testid` (`wrapper.get('[data-testid="save-entity-button"]')`). Never select by Vuetify classes (`.v-btn`), tag structure, or ids.
- Add `data-testid` to the component under test where needed. Name it `<what>-<kind>`: `entity-name-input`, `save-entity-button`, `entities-empty-state`.
- Assert on **what the user sees**: text (`toContain('Pump')`), visibility, `disabled`/`aria-*` attributes, and emitted events.
- Use `get()` when the element must exist (it fails clearly), and `find(...).exists()` only to assert that something is absent.

---

## 6. Setup

`vitest.config.ts` uses `jsdom`, includes `tests/unit/**` and `tests/integration/**`, sets `restoreMocks: true` and `unstubGlobals: true`, and inlines `vuetify`. `tests/setup.ts` polyfills `ResizeObserver` and starts the MSW server with `onUnhandledRequest: 'error'`, so any request without a handler fails the test. In component tests, where the API module is mocked, this also catches leaks to the real network.

`tests/utils/mount.ts` exports `mountWithPlugins(component, options)`. It creates Vuetify with the app's **real** theme config (so semantic theme keys exist), passes `global.plugins` (Vuetify, plus the router/pinia given in the options), and sets `global.stubs: { teleport: true }`. Vuetify dialogs, menus, and snackbars teleport into `document.body`, so without this stub their content is outside the wrapper and `wrapper.get(...)` can't find it.

Run everything: `npx vitest run`.

**jsdom limits:** Vuetify recommends a real browser for components that depend on layout, overlays, or real events (menus, `v-select` dropdowns, tooltips, virtual scrolling). If such a behavior can't be tested reliably in jsdom, test it in a browser test instead of fighting jsdom, and write that decision in `test-plan.md`.
