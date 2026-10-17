import { describe, expect, it, vi } from 'vitest'

import { createAssetType } from '@/api/asset-types'
import { makeAssetType } from '../../mocks/factories/asset-type'

describe('createAssetType', () => {
  it('returns the created asset type from the asset types path', async () => {
    const createdAssetType = makeAssetType({ id: 5, name: 'Valve' })
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(createdAssetType), { status: 201 }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await createAssetType({
      name: 'Valve',
      category: 'Mechanical',
      inspection_interval_days: 30,
    })

    expect(result).toEqual(createdAssetType)
  })
})
