import { apiRequest, apiRequestWithoutContent } from '@/api/client'
import type { ListParams, Page } from '@/models/page'
import type { Site, SiteInput } from '@/models/site'
import { buildListQuery } from '@/utils/list-params'

const SITES_PATH = '/atlas/sites'

const listSites = (params: ListParams): Promise<Page<Site>> => {
  return apiRequest<Page<Site>>(`${SITES_PATH}?${buildListQuery(params)}`)
}

const getSite = (siteId: number): Promise<Site> => {
  return apiRequest<Site>(`${SITES_PATH}/${siteId}`)
}

const createSite = (input: SiteInput): Promise<Site> => {
  return apiRequest<Site>(SITES_PATH, { method: 'POST', body: input })
}

const updateSite = (siteId: number, input: SiteInput): Promise<Site> => {
  return apiRequest<Site>(`${SITES_PATH}/${siteId}`, { method: 'PUT', body: input })
}

const deleteSite = (siteId: number): Promise<void> => {
  return apiRequestWithoutContent(`${SITES_PATH}/${siteId}`, { method: 'DELETE' })
}

export { createSite, deleteSite, getSite, listSites, updateSite }
