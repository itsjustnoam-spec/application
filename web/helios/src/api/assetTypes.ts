import { apiRequest } from '@/api/client'
import type { AssetType, AssetTypeInput } from '@/models/assetType'

const ASSET_TYPES_PATH = '/atlas/asset-types'

export const fetchAssetTypes = (): Promise<AssetType[]> => {
  return apiRequest<AssetType[]>(ASSET_TYPES_PATH)
}

export const createAssetType = (assetTypeInput: AssetTypeInput): Promise<AssetType> => {
  return apiRequest<AssetType>(ASSET_TYPES_PATH, { method: 'POST', body: assetTypeInput })
}

export const updateAssetType = (
  assetTypeId: number,
  assetTypeInput: AssetTypeInput,
): Promise<AssetType> => {
  return apiRequest<AssetType>(`${ASSET_TYPES_PATH}/${assetTypeId}`, {
    method: 'PUT',
    body: assetTypeInput,
  })
}

export const deleteAssetType = (assetTypeId: number): Promise<void> => {
  return apiRequest<void>(`${ASSET_TYPES_PATH}/${assetTypeId}`, { method: 'DELETE' })
}
