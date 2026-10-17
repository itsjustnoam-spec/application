import { apiRequest } from '@/api/client'
import type { AssetType, AssetTypeInput } from '@/models/asset-type'
import type { ListParams, Page } from '@/models/page'
import { buildListQuery } from '@/utils/list-params'

const ASSET_TYPES_PATH = '/atlas/asset-types'

export const listAssetTypes = (params: ListParams): Promise<Page<AssetType>> => {
  return apiRequest<Page<AssetType>>(`${ASSET_TYPES_PATH}?${buildListQuery(params)}`)
}

export const createAssetType = (input: AssetTypeInput): Promise<AssetType> => {
  return apiRequest<AssetType>(ASSET_TYPES_PATH, { method: 'POST', body: input })
}

export const updateAssetType = (assetTypeId: number, input: AssetTypeInput): Promise<AssetType> => {
  return apiRequest<AssetType>(`${ASSET_TYPES_PATH}/${assetTypeId}`, {
    method: 'PUT',
    body: input,
  })
}

export const archiveAssetType = (assetTypeId: number): Promise<void> => {
  return apiRequest<void>(`${ASSET_TYPES_PATH}/${assetTypeId}`, { method: 'DELETE' })
}
