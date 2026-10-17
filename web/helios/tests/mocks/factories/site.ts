import type { Page } from '@/models/page'
import type { Site } from '@/models/site'

const makeSite = (overrides: Partial<Site> = {}): Site => {
  return {
    id: 1,
    name: 'North Depot',
    address: '1 Main Street',
    timezone: 'Europe/Berlin',
    archived: false,
    ...overrides,
  }
}

const makeSitePage = (items: Site[] = [makeSite()]): Page<Site> => {
  return {
    items,
    total: items.length,
    limit: 20,
    offset: 0,
  }
}

export { makeSite, makeSitePage }
