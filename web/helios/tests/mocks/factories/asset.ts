import type { Asset } from '@/models/asset'
import type { Page } from '@/models/page'

const makeAsset = (overrides: Partial<Asset> = {}): Asset => {
  return {
    id: 1,
    name: 'Compressor',
    serial_number: 'SN-1',
    site_id: 1,
    site_name: 'North Depot',
    site_timezone: 'Europe/Berlin',
    asset_type_id: 1,
    asset_type_name: 'Pump',
    status: 'Operational',
    installation_date: '2026-01-01',
    notes: null,
    next_inspection_due: '2026-01-31',
    is_overdue: false,
    archived: false,
    ...overrides,
  }
}

const makeAssetPage = (items: Asset[] = [makeAsset()]): Page<Asset> => {
  return {
    items,
    total: items.length,
    limit: 20,
    offset: 0,
  }
}

export { makeAsset, makeAssetPage }
