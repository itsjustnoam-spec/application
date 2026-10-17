import { apiRequest, apiRequestWithoutContent } from '@/api/client'
import type { Asset, AssetInput } from '@/models/asset'
import type { ListParams, Page } from '@/models/page'
import { buildListQuery } from '@/utils/list-params'

const ASSETS_PATH = '/atlas/assets'

const listAssets = (params: ListParams): Promise<Page<Asset>> => {
  return apiRequest<Page<Asset>>(`${ASSETS_PATH}?${buildListQuery(params)}`)
}

const getAsset = (assetId: number): Promise<Asset> => {
  return apiRequest<Asset>(`${ASSETS_PATH}/${assetId}`)
}

const createAsset = (input: AssetInput): Promise<Asset> => {
  return apiRequest<Asset>(ASSETS_PATH, { method: 'POST', body: input })
}

const updateAsset = (assetId: number, input: AssetInput): Promise<Asset> => {
  return apiRequest<Asset>(`${ASSETS_PATH}/${assetId}`, { method: 'PUT', body: input })
}

const deleteAsset = (assetId: number): Promise<void> => {
  return apiRequestWithoutContent(`${ASSETS_PATH}/${assetId}`, { method: 'DELETE' })
}

export { createAsset, deleteAsset, getAsset, listAssets, updateAsset }
