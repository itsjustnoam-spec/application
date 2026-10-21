# Vitest Conventions Checklist

Run this per changed frontend Vitest file. Every item must be answered ✅, ❌ (with `file:line`), or N/A.

## All Vitest layers
- [ ] VT-01 File is in the right place for its layer (`tests/unit/<mirror>` for component/unit, `tests/integration/<feature>/` for integration) and ends in `.spec.ts`
- [ ] VT-02 One `describe` named after the unit (component) or `<Feature>: <flow>` (integration)
- [ ] VT-03 `it(...)` strings read as "<expected behavior> when <condition>" and match `test-plan.md` exactly
- [ ] VT-04 Arrange / Act / Assert separated by blank lines, with no comments
- [ ] VT-05 One behavior per test, with no loops or conditionals (`it.each` for variations)
- [ ] VT-06 Test data comes from typed factories in `tests/mocks/factories/`, overriding only the relevant fields
- [ ] VT-07 Elements selected by `data-testid`, never by Vuetify classes or DOM structure
- [ ] VT-08 Every `trigger`/`setValue`/`setProps` is awaited, and `flushPromises()` is used after network work (no sleeps)
- [ ] VT-09 No access to `wrapper.vm` internals and no calls to component methods
- [ ] VT-10 Every test has a meaningful assertion on visible output or emitted events (no snapshot-only tests, no `expect(true)`, not just "a mock was called")
- [ ] VT-11 Fresh Pinia/router per test, and no shared mutable state between tests
- [ ] VT-12 Debounce tests use fake timers and the component's named debounce constant
- [ ] VT-13 Explicit checks and named constants per `vue-conventions` inside test code
- [ ] VT-16 Each test reads top to bottom (DAMP): factories and mount helpers are fine, but the arrange step isn't hidden behind clever abstractions
- [ ] VT-17 `get()` is used when the element must exist, and `find(...).exists()` only to assert that something is absent
- [ ] VT-14 New tests are added to the existing spec file of their component or flow; no new file for a small case
- [ ] VT-15 Mock data and expected values are built by hand (factories with fixed values), never with the app's own functions (converters, mappers); importing types is fine

## Component tests
- [ ] VT-20 Uses `mount` (via `mountWithPlugins`), not `shallowMount`. Any stub is justified.
- [ ] VT-21 API is mocked at the app's API client module (`vi.mock('@/api/...')`), not at axios/fetch
- [ ] VT-22 Store uses `createTestingPinia({ createSpy: vi.fn })`, and action calls are asserted as the component's contract
- [ ] VT-24 Overlays (`v-dialog`, `v-menu`, `v-snackbar`) are queried inside the wrapper (teleport is stubbed), never through `document.body`
- [ ] VT-25 A component that uses the router gets a real memory-history router, awaited with `router.isReady()` before mounting
- [ ] VT-26 API errors are mocked with the same error type the real client throws (`mockRejectedValue(new ApiError(...))`)
- [ ] VT-27 An API call's arguments are asserted only when the call itself is the behavior, and always together with the visible result
- [ ] VT-23 Component tests exist only for shared components or components with important behavior, and cover their contract (emits, behavior-changing props), not every visual variation

## Integration tests
- [ ] VT-30 Mounts the real view with a real Pinia (actions not stubbed) and a real memory-history router
- [ ] VT-31 No `vi.mock` of app modules. Only the network is mocked, via MSW.
- [ ] VT-32 Per-test scenarios use `server.use(...)`, and mutation handlers validate the payload like the backend
- [ ] VT-33 No assertions on request details for requests with visible effects
- [ ] VT-34 Handler paths and payloads match `spec.md` §5
- [ ] VT-36 Fire-and-forget calls with no visible effect (analytics, audit) are asserted through MSW life-cycle events
- [ ] VT-37 Assertions are on the final visible DOM state, not on store state
- [ ] VT-35 The main flow, failures of important actions, and data-loss edge cases are covered; there are no tests for labels, styling, or every empty/loading state

## Coverage
- [ ] VT-40 No test exists only to raise coverage; there's no frontend coverage target
