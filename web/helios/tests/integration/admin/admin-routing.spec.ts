import { flushPromises } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory } from 'vue-router'
import { describe, expect, it } from 'vitest'

import App from '@/App.vue'
import { createAppRouter } from '@/router'
import { mountWithPlugins } from '../../utils/mount'

describe('Admin: routing', () => {
  it('redirects the admin route to the sites tab', async () => {
    const router = createAppRouter(createMemoryHistory())
    await router.push('/admin')
    await router.isReady()

    mountWithPlugins(App, {
      global: { plugins: [createPinia(), router] },
    })
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/admin/sites')
  })
})
