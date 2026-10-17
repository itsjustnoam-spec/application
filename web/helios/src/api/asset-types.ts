import { apiRequest, apiRequestWithoutContent } from '@/api/client'
import type { AssetType, AssetTypeInput } from '@/models/asset-type'
import type { ListParams, Page } from '@/models/page'
import { buildListQuery } from '@/utils/list-params'

const ASSET_TYPES_PATH = '/atlas/asset-types'

const listAssetTypes = (params: ListParams): Promise<Page<AssetType>> => {
  return apiRequest<Page<AssetType>>(`${ASSET_TYPES_PATH}?${buildListQuery(params)}`)
}

const getAssetType = (assetTypeId: number): Promise<AssetType> => {
  return apiRequest<AssetType>(`${ASSET_TYPES_PATH}/${assetTypeId}`)
}

const createAssetType = (input: AssetTypeInput): Promise<AssetType> => {
  return apiRequest<AssetType>(ASSET_TYPES_PATH, { method: 'POST', body: input })
}

const updateAssetType = (assetTypeId: number, input: AssetTypeInput): Promise<AssetType> => {
  return apiRequest<AssetType>(`${ASSET_TYPES_PATH}/${assetTypeId}`, {
    method: 'PUT',
    body: input,
  })
}

const deleteAssetType = (assetTypeId: number): Promise<void> => {
  return apiRequestWithoutContent(`${ASSET_TYPES_PATH}/${assetTypeId}`, { method: 'DELETE' })
}

export {
  createAssetType,
  deleteAssetType,
  getAssetType,
  listAssetTypes,
  updateAssetType,
}
