import { http, HttpResponse } from 'msw'

import type { AssetTypeInput } from '@/models/asset-type'

import { makeAssetType, makeAssetTypePage } from '../factories/asset-type'

export const listAssetTypesHandler = http.get('/api/atlas/asset-types', () => {
  return HttpResponse.json(makeAssetTypePage())
})

export const createAssetTypeHandler = http.post('/api/atlas/asset-types', async ({ request }) => {
  const body = (await request.json()) as AssetTypeInput
  if (body.inspection_interval_days < 1 || body.inspection_interval_days > 3650) {
    return HttpResponse.json({ detail: 'Interval out of range.' }, { status: 422 })
  }
  return HttpResponse.json(
    makeAssetType({
      name: body.name,
      category: body.category,
      inspection_interval_days: body.inspection_interval_days,
    }),
    { status: 201 },
  )
})

export const archiveAssetTypeHandler = http.delete('/api/atlas/asset-types/:assetTypeId', () => {
  return new HttpResponse(null, { status: 204 })
})
