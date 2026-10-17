import type { AssetType } from '@/models/assetType'

export const makeAssetType = (overrides: Partial<AssetType> = {}): AssetType => {
  return {
    id: 1,
    name: 'Centrifugal pump',
    category: 'Rotating equipment',
    inspection_interval_days: 90,
    ...overrides,
  }
}
