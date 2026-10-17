import type { Page } from '@/models/page'

interface Site {
  id: number
  name: string
  address: string
  timezone: string
  archived: boolean
}

interface SiteInput {
  name: string
  address: string
  timezone: string
}

type SitePage = Page<Site>

export type { Site, SiteInput, SitePage }
