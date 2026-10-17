import { flushPromises } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import ConfirmDeleteDialog from '@/components/ConfirmDeleteDialog.vue'
import AssetsView from '@/views/AssetsView.vue'
import { makeAsset, makeAssetPage } from '../../mocks/factories/asset'
import { server } from '../../mocks/server'
import { mountWithPlugins } from '../../utils/mount'

const OVERDUE_ROW_CLASS = 'asset-row-overdue'
const NO_MATCH_MESSAGE = 'No assets match these filters.'
const SITE_FILTER_TEST_ID = 'asset-site-filter'
const NORTH_DEPOT_NAME = 'North Depot'

const mountAssetsView = async () => {
  const wrapper = mountWithPlugins(AssetsView)
  await flushPromises()
  return wrapper
}

describe('Assets: list', () => {
  it('lists assets and highlights the one whose next inspection is overdue', async () => {
    server.use(
      http.get('/api/atlas/assets', () =>
        HttpResponse.json(
          makeAssetPage([
            makeAsset({ id: 1, name: 'Overdue pump', is_overdue: true }),
            makeAsset({ id: 2, name: 'Current valve', is_overdue: false }),
          ]),
        ),
      ),
    )
    const wrapper = await mountAssetsView()

    const rows = wrapper.findAll('[data-testid="asset-row"]')

    expect(rows[0].classes()).toContain(OVERDUE_ROW_CLASS)
    expect(rows[1].classes()).not.toContain(OVERDUE_ROW_CLASS)
    expect(wrapper.findAll('[data-testid="asset-overdue-chip"]')).toHaveLength(1)
    expect(wrapper.get('[data-testid="asset-overdue-chip"]').text()).toBe('Overdue')
  })

  it('shows the empty message when no assets match the filters', async () => {
    server.use(http.get('/api/atlas/assets', () => HttpResponse.json(makeAssetPage([]))))
    const wrapper = await mountAssetsView()

    expect(wrapper.text()).toContain(NO_MATCH_MESSAGE)
    expect(wrapper.find('[data-testid="assets-error"]').exists()).toBe(false)
  })

  it('sends the chosen site as a filter when the site filter changes', async () => {
    let lastSearchParams = new URLSearchParams()
    server.use(
      http.get('/api/atlas/assets', ({ request }) => {
        lastSearchParams = new URL(request.url).searchParams
        return HttpResponse.json(makeAssetPage())
      }),
    )
    const wrapper = await mountAssetsView()

    const siteFilterInput = wrapper.get(`[data-testid="${SITE_FILTER_TEST_ID}"] input`)
    await siteFilterInput.setValue(NORTH_DEPOT_NAME)
    await siteFilterInput.trigger('keydown', { key: 'Enter' })
    await flushPromises()

    expect(lastSearchParams.get('site_id')).toBe('1')
    expect(lastSearchParams.get('offset')).toBe('0')
  })

  it('shows the error with a retry button when loading assets fails', async () => {
    let attempts = 0
    server.use(
      http.get('/api/atlas/assets', () => {
        attempts += 1
        if (attempts === 1) {
          return HttpResponse.json({ detail: 'Unavailable' }, { status: 503 })
        }
        return HttpResponse.json(makeAssetPage([makeAsset({ name: 'Compressor' })]))
      }),
    )
    const wrapper = await mountAssetsView()
    const errorBeforeRetry = wrapper.find('[data-testid="assets-error"]').exists()

    await wrapper.get('[data-testid="retry-assets-button"]').trigger('click')
    await flushPromises()

    expect(errorBeforeRetry).toBe(true)
    expect(wrapper.find('[data-testid="assets-error"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Compressor')
  })
})

describe('Assets: archive', () => {
  it('shows the server message when archiving an asset fails', async () => {
    server.use(
      http.delete('/api/atlas/assets/:assetId', () =>
        HttpResponse.json({ detail: 'Asset not found' }, { status: 404 }),
      ),
    )
    const wrapper = await mountAssetsView()

    await wrapper.get('[data-testid="archive-asset-button"]').trigger('click')
    const confirmDialog = wrapper.findComponent(ConfirmDeleteDialog)
    await confirmDialog.get('[data-testid="confirm-delete-button"]').trigger('click')
    await flushPromises()

    expect(confirmDialog.get('[data-testid="confirm-delete-error"]').text()).toContain(
      'Asset not found',
    )
  })

  it('archives the asset and removes it from the list after confirming', async () => {
    let assets = [makeAsset()]
    server.use(
      http.get('/api/atlas/assets', () => HttpResponse.json(makeAssetPage(assets))),
      http.delete('/api/atlas/assets/:assetId', ({ params }) => {
        assets = assets.filter((asset) => String(asset.id) !== params.assetId)
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const wrapper = await mountAssetsView()

    await wrapper.get('[data-testid="archive-asset-button"]').trigger('click')
    await wrapper.findComponent(ConfirmDeleteDialog).get('[data-testid="confirm-delete-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).not.toContain('Compressor')
  })

  it('closes the archive dialog without archiving when cancel is clicked', async () => {
    let archiveRequestCount = 0
    server.use(
      http.delete('/api/atlas/assets/:assetId', () => {
        archiveRequestCount += 1
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const wrapper = await mountAssetsView()

    await wrapper.get('[data-testid="archive-asset-button"]').trigger('click')
    await wrapper.findComponent(ConfirmDeleteDialog).get('[data-testid="cancel-delete-button"]').trigger('click')
    await flushPromises()

    expect(archiveRequestCount).toBe(0)
    expect(wrapper.findComponent(ConfirmDeleteDialog).isVisible()).toBe(false)
    expect(wrapper.text()).toContain('Compressor')
  })
})
