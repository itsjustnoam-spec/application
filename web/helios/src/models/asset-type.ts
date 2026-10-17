const ASSET_CATEGORIES = ['Electrical', 'Mechanical', 'HVAC', 'Safety', 'Other'] as const

type AssetCategory = (typeof ASSET_CATEGORIES)[number]

interface AssetType {
  id: number
  name: string
  category: AssetCategory
  inspection_interval_days: number
  archived: boolean
}

interface AssetTypeInput {
  name: string
  category: AssetCategory
  inspection_interval_days: number
}

export type { AssetCategory, AssetType, AssetTypeInput }
export { ASSET_CATEGORIES }
