import type { AssetType } from '@/models/asset-type'
import type { Page } from '@/models/page'

export const makeAssetType = (overrides: Partial<AssetType> = {}): AssetType => {
  return {
    id: 1,
    name: 'Pump',
    category: 'Mechanical',
    inspection_interval_days: 30,
    archived: false,
    ...overrides,
  }
}

export const makeAssetTypePage = (items: AssetType[] = [makeAssetType()]): Page<AssetType> => {
  return {
    items,
    total: items.length,
    limit: 20,
    offset: 0,
  }
}
