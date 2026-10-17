import type { Page } from '@/models/page'

const ASSET_STATUSES = ['Operational', 'Needs attention', 'Out of service', 'Retired'] as const

type AssetStatus = (typeof ASSET_STATUSES)[number]

interface Asset {
  id: number
  name: string
  serial_number: string
  site_id: number
  site_name: string
  site_timezone: string
  asset_type_id: number
  asset_type_name: string
  status: AssetStatus
  installation_date: string
  notes: string | null
  next_inspection_due: string | null
  is_overdue: boolean
  archived: boolean
}

interface AssetInput {
  name: string
  serial_number: string
  site_id: number
  asset_type_id: number
  status: AssetStatus
  installation_date: string
  notes: string | null
}

type AssetPage = Page<Asset>

export type { Asset, AssetInput, AssetPage, AssetStatus }
export { ASSET_STATUSES }
