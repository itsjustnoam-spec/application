# Frontend Integration Tests (Vitest + Vue Test Utils + MSW)

An integration test mounts **a whole view or feature**: the real components, the real Pinia store, the real router, and the real API client. It replaces **only the network**, using MSW. It proves that the pieces work together the way a user experiences them. This is the highest-confidence Vitest layer: most frontend confidence should come from here, and component tests fill in the details.

## 1. What to cover per view/feature
Only the important behavior (see "What Gets a Frontend Test" in `SKILL.md`):
- [ ] **The main flow** from the spec, end to end within the view (e.g. open → list loads → create → the list shows the new item)
- [ ] **Failures that matter**: backend errors on important actions (save, delete, archive) show a message and leave the UI usable. Not every error state of every request.
- [ ] **Shared wiring**: store or composable behavior that several components depend on
- [ ] **Frontend edge cases `EC-n`** where a bug would lose or corrupt data (duplicate submit, stale responses overwriting newer ones)

Don't add tests for every empty state, label, or navigation detail.

## 2. Setup rules
- **Pinia:** a real store, fresh per test: `const pinia = createPinia()` (or `createTestingPinia({ stubActions: false, createSpy: vi.fn })` if spies are needed). Never stub actions in integration tests.
- **Router:** a real router with the app's real routes, fresh per test: `createRouter({ history: createMemoryHistory(), routes })`. Then `await router.push('/entities')` and `await router.isReady()` before mounting.
- **Mount the route's view** (or `App`/`RouterView` when testing navigation) through `mountWithPlugins` with that pinia and router.
- **No `vi.mock` of the app's own modules.** If you need to mock an API module, you're writing a component test, not an integration test.

## 3. Network with MSW
- Happy-path handlers live in `tests/mocks/handlers/<domain>.ts` and return factory data. The server (`tests/mocks/server.ts`) is started in `tests/setup.ts` with `onUnhandledRequest: 'error'`.
- Per-test scenarios use runtime overrides, which are reset after each test:
  ```ts
  server.use(http.get('/api/entities', () => HttpResponse.json({ detail: 'Database unavailable' }, { status: 503 })))
  ```
- **Don't assert on requests** (that a request was sent, its URL, or its body). That's an implementation detail. Instead, **validate in the handler**, returning the realistic error the backend would send when the request is wrong. The UI then shows the error, and the test fails on the visible result:
  ```ts
  http.post('/api/entities', async ({ request }) => {
    const body = (await request.json()) as CreateEntityRequest
    if (body.name.trim().length === 0) {
      return HttpResponse.json({ detail: 'Name is required.' }, { status: 422 })
    }
    return HttpResponse.json(makeEntity({ name: body.name }), { status: 201 })
  })
  ```
- The exception is fire-and-forget calls with no visible effect (analytics, audit pings). Assert those through MSW life-cycle events (`server.events.on('request:start', ...)`).
- Handler paths and payloads must match `spec.md` §5 exactly. They are the contract.

## 4. Async rules
- After every action that causes requests: `await flushPromises()`. If a flow chains several requests, flush after each step that triggers one.
- Assert the final visible state, not intermediate store state.

## 5. Example
```ts
import { flushPromises } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import { createPinia } from 'pinia'
import { describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import EntitiesView from '@/views/EntitiesView.vue'
import { routes } from '@/router/routes'
import { server } from '../../mocks/server'
import { mountWithPlugins } from '../../utils/mount'

const mountEntitiesView = async () => {
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push('/entities')
  await router.isReady()
  const wrapper = mountWithPlugins(EntitiesView, { pinia: createPinia(), router })
  await flushPromises()
  return wrapper
}

describe('Entities: create flow', () => {
  it('lists the created entity after the create dialog is submitted', async () => {
    const wrapper = await mountEntitiesView()

    await wrapper.get('[data-testid="open-create-entity-button"]').trigger('click')
    await wrapper.get('[data-testid="entity-name-input"] input').setValue('Pump')
    await wrapper.get('[data-testid="save-entity-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('[data-testid="entities-table"]').text()).toContain('Pump')
  })

  it('shows the backend error when loading entities fails', async () => {
    server.use(http.get('/api/entities', () => HttpResponse.json({ detail: 'Database unavailable' }, { status: 503 })))

    const wrapper = await mountEntitiesView()

    expect(wrapper.get('[data-testid="entities-error"]').text()).toContain('Database unavailable')
  })
})
```

## 6. Forbidden in integration tests
- `vi.mock` of app modules (API client, stores, composables)
- Stubbed store actions, or a hand-built fake router
- Asserting MSW request details for requests that have visible effects
- Asserting store internals instead of the DOM
- Handlers that accept any payload for mutations (they must validate like the backend)
