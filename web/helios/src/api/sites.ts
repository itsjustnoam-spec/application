import { apiRequest } from '@/api/client'
import type { ListParams, Page } from '@/models/page'
import type { Site, SiteInput } from '@/models/site'
import { buildListQuery } from '@/utils/list-params'

const SITES_PATH = '/atlas/sites'

export const listSites = (params: ListParams): Promise<Page<Site>> => {
  return apiRequest<Page<Site>>(`${SITES_PATH}?${buildListQuery(params)}`)
}

export const createSite = (input: SiteInput): Promise<Site> => {
  return apiRequest<Site>(SITES_PATH, { method: 'POST', body: input })
}

export const updateSite = (siteId: number, input: SiteInput): Promise<Site> => {
  return apiRequest<Site>(`${SITES_PATH}/${siteId}`, { method: 'PUT', body: input })
}

export const getSite = (siteId: number): Promise<Site> => {
  return apiRequest<Site>(`${SITES_PATH}/${siteId}`)
}

export const deleteSite = (siteId: number): Promise<void> => {
  return apiRequest<void>(`${SITES_PATH}/${siteId}`, { method: 'DELETE' })
}
