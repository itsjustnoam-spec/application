import { flushPromises } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { SEARCH_DEBOUNCE_MS } from '@/utils/use-paged-list'
import ConfirmDeleteDialog from '@/components/ConfirmDeleteDialog.vue'
import SiteFormDialog from '@/components/SiteFormDialog.vue'
import SitesView from '@/views/SitesView.vue'
import { makeSite, makeSitePage } from '../../mocks/factories/site'
import { server } from '../../mocks/server'
import { mountWithPlugins } from '../../utils/mount'

const mountSitesView = async () => {
  const wrapper = mountWithPlugins(SitesView)
  await flushPromises()
  return wrapper
}

afterEach(() => {
  vi.useRealTimers()
})

describe('Admin: sites', () => {

  it('creates a site and shows it in the list', async () => {
    let sites = [makeSite()]
    server.use(
      http.get('/api/atlas/sites', () => HttpResponse.json(makeSitePage(sites))),
      http.post('/api/atlas/sites', async ({ request }) => {
        const body = (await request.json()) as { name: string; address: string }
        const createdSite = makeSite({ id: 2, name: body.name, address: body.address })
        sites = [...sites, createdSite]
        return HttpResponse.json(createdSite, { status: 201 })
      }),
    )
    const wrapper = await mountSitesView()

    await wrapper.get('[data-testid="create-site-button"]').trigger('click')
    const formDialog = wrapper.findComponent(SiteFormDialog)
    await formDialog.get('[data-testid="site-name-input"] input').setValue('Harbour Yard')
    await formDialog.get('[data-testid="site-address-input"] input').setValue('4 Quay Street')
    await formDialog.get('[data-testid="site-timezone-input"] input').setValue('Europe/Berlin')
    await formDialog.get('[data-testid="site-timezone-input"] input').trigger('keydown', { key: 'Enter' })
    await formDialog.get('[data-testid="site-form-save-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Harbour Yard')
  })

  it('shows only the sites matching the search text after the debounce', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    server.use(
      http.get('/api/atlas/sites', ({ request }) => {
        const query = new URL(request.url).searchParams.get('q') ?? ''
        const allSites = [
          makeSite({ id: 1, name: 'North Depot' }),
          makeSite({ id: 2, name: 'South Depot' }),
        ]
        return HttpResponse.json(
          makeSitePage(allSites.filter((site) => site.name.toLowerCase().includes(query.toLowerCase()))),
        )
      }),
    )
    const wrapper = await mountSitesView()

    await wrapper.get('[data-testid="site-search-input"] input').setValue('north')
    vi.advanceTimersByTime(SEARCH_DEBOUNCE_MS)
    await flushPromises()

    expect(wrapper.text()).toContain('North Depot')
    expect(wrapper.text()).not.toContain('South Depot')
  })

  it('removes a site from the list after the archive is confirmed', async () => {
    let sites = [makeSite()]
    server.use(
      http.get('/api/atlas/sites', () => HttpResponse.json(makeSitePage(sites))),
      http.delete('/api/atlas/sites/:siteId', ({ params }) => {
        sites = sites.filter((site) => String(site.id) !== params.siteId)
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const wrapper = await mountSitesView()

    await wrapper.get('[data-testid="archive-site-button"]').trigger('click')
    await wrapper.findComponent(ConfirmDeleteDialog).get('[data-testid="confirm-delete-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).not.toContain('North Depot')
  })

  it('updates a site and shows its new name in the list', async () => {
    let sites = [makeSite()]
    server.use(
      http.get('/api/atlas/sites', () => HttpResponse.json(makeSitePage(sites))),
      http.put('/api/atlas/sites/:siteId', async ({ request, params }) => {
        const body = (await request.json()) as { name: string; address: string; timezone: string }
        const updatedSite = makeSite({ id: Number(params.siteId), ...body })
        sites = [updatedSite]
        return HttpResponse.json(updatedSite)
      }),
    )
    const wrapper = await mountSitesView()

    await wrapper.get('[data-testid="edit-site-button"]').trigger('click')
    const formDialog = wrapper.findComponent(SiteFormDialog)
    await formDialog.get('[data-testid="site-name-input"] input').setValue('Renamed Depot')
    await formDialog.get('[data-testid="site-form-save-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Renamed Depot')
  })

  it('shows the server error when archiving a site fails', async () => {
    server.use(
      http.delete('/api/atlas/sites/:siteId', () =>
        HttpResponse.json({ detail: 'The site is linked to open work orders.' }, { status: 409 }),
      ),
    )
    const wrapper = await mountSitesView()

    await wrapper.get('[data-testid="archive-site-button"]').trigger('click')
    const confirmDialog = wrapper.findComponent(ConfirmDeleteDialog)
    await confirmDialog.get('[data-testid="confirm-delete-button"]').trigger('click')
    await flushPromises()

    expect(confirmDialog.get('[data-testid="confirm-delete-error"]').text()).toContain(
      'The site is linked to open work orders.',
    )
  })

  it('loads the next page of sites when the next page button is clicked', async () => {
    server.use(
      http.get('/api/atlas/sites', ({ request }) => {
        const offset = Number(new URL(request.url).searchParams.get('offset'))
        const pageSite =
          offset === 0
            ? makeSite({ id: 1, name: 'North Depot' })
            : makeSite({ id: 21, name: 'Page Two Depot' })
        return HttpResponse.json({ items: [pageSite], total: 21, limit: 20, offset })
      }),
    )
    const wrapper = await mountSitesView()

    await wrapper.get('[data-testid="v-pagination-next"] button').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Page Two Depot')
  })

  it('shows only the results of the latest search when an older request finishes last', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    let releaseNorthRequest: () => void = () => {}
    server.use(
      http.get('/api/atlas/sites', async ({ request }) => {
        const query = new URL(request.url).searchParams.get('q') ?? ''
        if (query === 'north') {
          await new Promise<void>((resolve) => {
            releaseNorthRequest = resolve
          })
          return HttpResponse.json(makeSitePage([makeSite({ id: 1, name: 'North Depot' })]))
        }
        return HttpResponse.json(makeSitePage([makeSite({ id: 2, name: 'South Depot' })]))
      }),
    )
    const wrapper = await mountSitesView()
    const searchInput = wrapper.get('[data-testid="site-search-input"] input')

    await searchInput.setValue('north')
    vi.advanceTimersByTime(SEARCH_DEBOUNCE_MS)
    await flushPromises()
    await searchInput.setValue('south')
    vi.advanceTimersByTime(SEARCH_DEBOUNCE_MS)
    await flushPromises()
    releaseNorthRequest()
    await flushPromises()

    expect(wrapper.text()).toContain('South Depot')
    expect(wrapper.text()).not.toContain('North Depot')
  })

  it('moves to the previous page when the last row of the last page is archived', async () => {
    let isPageTwoArchived = false
    server.use(
      http.get('/api/atlas/sites', ({ request }) => {
        const offset = Number(new URL(request.url).searchParams.get('offset'))
        const total = isPageTwoArchived ? 20 : 21
        if (offset === 0) {
          return HttpResponse.json({
            items: [makeSite({ id: 1, name: 'North Depot' })],
            total,
            limit: 20,
            offset,
          })
        }
        const items = isPageTwoArchived ? [] : [makeSite({ id: 21, name: 'Page Two Depot' })]
        return HttpResponse.json({ items, total, limit: 20, offset })
      }),
      http.delete('/api/atlas/sites/:siteId', () => {
        isPageTwoArchived = true
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const wrapper = await mountSitesView()
    await wrapper.get('[data-testid="v-pagination-next"] button').trigger('click')
    await flushPromises()

    await wrapper.get('[data-testid="archive-site-button"]').trigger('click')
    await wrapper.findComponent(ConfirmDeleteDialog).get('[data-testid="confirm-delete-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('North Depot')
  })

  it('keeps the site in the list when the archive confirmation is cancelled', async () => {
    const wrapper = await mountSitesView()

    await wrapper.get('[data-testid="archive-site-button"]').trigger('click')
    await wrapper.findComponent(ConfirmDeleteDialog).get('[data-testid="cancel-delete-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('North Depot')
  })
})
