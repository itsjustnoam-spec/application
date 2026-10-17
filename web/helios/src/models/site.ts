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

export type { Site, SiteInput }
