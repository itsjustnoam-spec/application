import { createPinia } from 'pinia'
import { createMemoryHistory } from 'vue-router'
import { http, HttpResponse } from 'msw'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import { SERVER_ERROR_MESSAGE } from '@/api/errors'
import DashboardView from '@/views/DashboardView.vue'
import { createAppRouter } from '@/router'

import { server } from '../../mocks/server'
import { mountWithPlugins } from '../../utils/mount'

describe('Dashboard: atlas health', () => {
  it('shows the atlas service status after the health request succeeds', async () => {
    const wrapper = mountWithPlugins(DashboardView, {
      global: { plugins: [createPinia(), createAppRouter(createMemoryHistory())] },
    })

    await flushPromises()

    expect(wrapper.get('[data-testid="atlas-health-status"]').text()).toContain('ok')
  })

  it('shows an error message when the atlas health request fails', async () => {
    server.use(
      http.get('/api/atlas/health', () => {
        return HttpResponse.json({ detail: 'unavailable' }, { status: 503 })
      }),
    )
    const wrapper = mountWithPlugins(DashboardView, {
      global: { plugins: [createPinia(), createAppRouter(createMemoryHistory())] },
    })

    await flushPromises()

    expect(wrapper.get('[data-testid="atlas-health-error"]').text()).toContain(
      SERVER_ERROR_MESSAGE,
    )
  })
})
