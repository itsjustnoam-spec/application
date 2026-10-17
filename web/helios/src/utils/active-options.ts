import { listAssetTypes } from '@/api/asset-types'
import { listSites } from '@/api/sites'
import type { SelectOption } from '@/models/select-option'

const OPTION_LIMIT = 20

const fetchActiveSiteOptions = async (query: string): Promise<SelectOption[]> => {
  const page = await listSites({ limit: OPTION_LIMIT, offset: 0, query })
  return page.items.map((site) => ({ value: site.id, title: site.name }))
}

const fetchActiveAssetTypeOptions = async (query: string): Promise<SelectOption[]> => {
  const page = await listAssetTypes({ limit: OPTION_LIMIT, offset: 0, query })
  return page.items.map((assetType) => ({ value: assetType.id, title: assetType.name }))
}

export { fetchActiveAssetTypeOptions, fetchActiveSiteOptions }
