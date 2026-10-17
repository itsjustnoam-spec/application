import { http, HttpResponse } from 'msw'

import { makeAssetType } from '../factories/assetTypes'

export const listAssetTypesHandler = http.get('/api/atlas/asset-types', () => {
  return HttpResponse.json([makeAssetType()])
})

export const createAssetTypeHandler = http.post('/api/atlas/asset-types', () => {
  return HttpResponse.json(makeAssetType(), { status: 201 })
})

export const updateAssetTypeHandler = http.put('/api/atlas/asset-types/:assetTypeId', () => {
  return HttpResponse.json(makeAssetType())
})

export const deleteAssetTypeHandler = http.delete('/api/atlas/asset-types/:assetTypeId', () => {
  return new HttpResponse(null, { status: 204 })
})
