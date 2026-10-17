import { flushPromises } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import { updateAssetType } from '@/api/asset-types'
import AssetTypeFormDialog from '@/components/AssetTypeFormDialog.vue'
import { makeAssetType } from '../../mocks/factories/asset-type'
import { mountWithPlugins } from '../../utils/mount'

vi.mock('@/api/asset-types')

const INTERVAL_RANGE_MESSAGE = 'Enter a whole number of days from 1 to 3650.'
const ASSET_TYPE_NAME_TAKEN_DETAIL = 'An asset type with this name already exists.'

describe('AssetTypeFormDialog', () => {
  it('shows the interval range message for an interval outside 1 to 3650', async () => {
    const wrapper = mountWithPlugins(AssetTypeFormDialog, {
      props: { assetType: makeAssetType() },
      global: { stubs: { teleport: true } },
    })

    await wrapper.get('[data-testid="asset-type-interval-input"] input').setValue('0')
    await wrapper.get('[data-testid="asset-type-form-save-button"]').trigger('click')

    expect(wrapper.text()).toContain(INTERVAL_RANGE_MESSAGE)
  })

  it('emits cancel when the cancel button is clicked', async () => {
    const wrapper = mountWithPlugins(AssetTypeFormDialog, {
      props: { assetType: null },
      global: { stubs: { teleport: true } },
    })

    await wrapper.get('[data-testid="asset-type-form-cancel-button"]').trigger('click')

    expect(wrapper.emitted('cancel')).toHaveLength(1)
  })

  it('emits saved with the updated asset type after a valid submit', async () => {
    const savedAssetType = makeAssetType({ id: 1, name: 'Compressor' })
    vi.mocked(updateAssetType).mockResolvedValue(savedAssetType)
    const wrapper = mountWithPlugins(AssetTypeFormDialog, {
      props: { assetType: makeAssetType({ id: 1 }) },
      global: { stubs: { teleport: true } },
    })

    await wrapper.get('[data-testid="asset-type-name-input"] input').setValue('Compressor')
    await wrapper.get('[data-testid="asset-type-form-save-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.emitted('saved')).toEqual([[savedAssetType]])
  })

  it('shows the backend detail when the server rejects a duplicate asset type name', async () => {
    vi.mocked(updateAssetType).mockRejectedValue(
      new ApiError(409, ASSET_TYPE_NAME_TAKEN_DETAIL),
    )
    const wrapper = mountWithPlugins(AssetTypeFormDialog, {
      props: { assetType: makeAssetType({ id: 1 }) },
      global: { stubs: { teleport: true } },
    })

    await wrapper.get('[data-testid="asset-type-form-save-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('[data-testid="asset-type-form-error"]').text()).toContain(
      ASSET_TYPE_NAME_TAKEN_DETAIL,
    )
  })
})
