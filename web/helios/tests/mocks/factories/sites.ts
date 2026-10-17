import type { Site } from '@/models/site'

export const makeSite = (overrides: Partial<Site> = {}): Site => {
  return {
    id: 1,
    name: 'North Plant',
    address: '12 Industrial Way',
    timezone: 'Europe/Berlin',
    ...overrides,
  }
}
