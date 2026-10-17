export interface AssetType {
  id: number
  name: string
  category: string
  inspection_interval_days: number
}

export interface AssetTypeInput {
  name: string
  category: string
  inspection_interval_days: number
}
