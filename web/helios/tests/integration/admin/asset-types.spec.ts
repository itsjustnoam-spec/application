import { flushPromises } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { SERVER_ERROR_MESSAGE } from '@/api/errors'
import AssetTypeFormDialog from '@/components/AssetTypeFormDialog.vue'
import ConfirmDeleteDialog from '@/components/ConfirmDeleteDialog.vue'
import AssetTypesView from '@/views/AssetTypesView.vue'
import { makeAssetType, makeAssetTypePage } from '../../mocks/factories/asset-type'
import { server } from '../../mocks/server'
import { mountWithPlugins } from '../../utils/mount'

const mountAssetTypesView = async () => {
  const wrapper = mountWithPlugins(AssetTypesView)
  await flushPromises()
  return wrapper
}

describe('Admin: asset types', () => {
  it('shows the empty state when there are no asset types', async () => {
    server.use(
      http.get('/api/atlas/asset-types', () => HttpResponse.json(makeAssetTypePage([]))),
    )

    const wrapper = await mountAssetTypesView()

    expect(wrapper.get('[data-testid="asset-types-empty"]').text()).toContain(
      'No asset types yet.',
    )
  })

  it('lists asset types with their category and interval', async () => {
    const wrapper = await mountAssetTypesView()

    expect(wrapper.text()).toContain('Pump')
    expect(wrapper.text()).toContain('Mechanical')
    expect(wrapper.text()).toContain('30')
  })

  it('updates an asset type and shows its new values in the list', async () => {
    let assetTypes = [makeAssetType()]
    server.use(
      http.get('/api/atlas/asset-types', () => HttpResponse.json(makeAssetTypePage(assetTypes))),
      http.put('/api/atlas/asset-types/:assetTypeId', async ({ request, params }) => {
        const body = (await request.json()) as { name: string; inspection_interval_days: number }
        const updatedAssetType = makeAssetType({
          id: Number(params.assetTypeId),
          name: body.name,
          inspection_interval_days: body.inspection_interval_days,
        })
        assetTypes = [updatedAssetType]
        return HttpResponse.json(updatedAssetType)
      }),
    )
    const wrapper = await mountAssetTypesView()

    await wrapper.get('[data-testid="edit-asset-type-button"]').trigger('click')
    const formDialog = wrapper.findComponent(AssetTypeFormDialog)
    await formDialog.get('[data-testid="asset-type-name-input"] input').setValue('Compressor')
    await formDialog.get('[data-testid="asset-type-interval-input"] input').setValue('60')
    await formDialog.get('[data-testid="asset-type-form-save-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Compressor')
    expect(wrapper.text()).toContain('60')
  })

  it('shows the error state with retry when loading asset types fails', async () => {
    server.use(
      http.get(
        '/api/atlas/asset-types',
        () => HttpResponse.json({ detail: 'Database unavailable' }, { status: 503 }),
        { once: true },
      ),
    )

    const wrapper = await mountAssetTypesView()

    expect(wrapper.get('[data-testid="asset-types-error"]').text()).toContain(SERVER_ERROR_MESSAGE)
    await wrapper.get('[data-testid="retry-asset-types-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Pump')
  })

  it('opens an empty dialog when the add asset type button is clicked', async () => {
    const wrapper = await mountAssetTypesView()

    await wrapper.get('[data-testid="create-asset-type-button"]').trigger('click')
    const nameInput = wrapper
      .findComponent(AssetTypeFormDialog)
      .get('[data-testid="asset-type-name-input"] input')

    expect(nameInput.element).toHaveProperty('value', '')
  })

  it('shows the server error when archiving an asset type fails', async () => {
    server.use(
      http.delete('/api/atlas/asset-types/:assetTypeId', () =>
        HttpResponse.json({ detail: 'The asset type is used by assets.' }, { status: 409 }),
      ),
    )
    const wrapper = await mountAssetTypesView()

    await wrapper.get('[data-testid="archive-asset-type-button"]').trigger('click')
    const confirmDialog = wrapper.findComponent(ConfirmDeleteDialog)
    await confirmDialog.get('[data-testid="confirm-delete-button"]').trigger('click')
    await flushPromises()

    expect(confirmDialog.get('[data-testid="confirm-delete-error"]').text()).toContain(
      'The asset type is used by assets.',
    )
  })

  it('removes an asset type from the list after the archive is confirmed', async () => {
    let assetTypes = [makeAssetType()]
    server.use(
      http.get('/api/atlas/asset-types', () => HttpResponse.json(makeAssetTypePage(assetTypes))),
      http.delete('/api/atlas/asset-types/:assetTypeId', ({ params }) => {
        assetTypes = assetTypes.filter((assetType) => String(assetType.id) !== params.assetTypeId)
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const wrapper = await mountAssetTypesView()

    await wrapper.get('[data-testid="archive-asset-type-button"]').trigger('click')
    await wrapper.findComponent(ConfirmDeleteDialog).get('[data-testid="confirm-delete-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).not.toContain('Pump')
  })
})
