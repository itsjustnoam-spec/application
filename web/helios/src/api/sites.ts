import { apiRequest } from '@/api/client'
import type { Site, SiteInput } from '@/models/site'

const SITES_PATH = '/atlas/sites'

export const fetchSites = (): Promise<Site[]> => {
  return apiRequest<Site[]>(SITES_PATH)
}

export const createSite = (siteInput: SiteInput): Promise<Site> => {
  return apiRequest<Site>(SITES_PATH, { method: 'POST', body: siteInput })
}

export const updateSite = (siteId: number, siteInput: SiteInput): Promise<Site> => {
  return apiRequest<Site>(`${SITES_PATH}/${siteId}`, { method: 'PUT', body: siteInput })
}

export const deleteSite = (siteId: number): Promise<void> => {
  return apiRequest<void>(`${SITES_PATH}/${siteId}`, { method: 'DELETE' })
}
