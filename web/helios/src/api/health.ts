import { apiRequest } from '@/api/client'
import type { HealthStatus } from '@/models/health'

const ATLAS_HEALTH_PATH = '/atlas/health'

const fetchAtlasHealth = (): Promise<HealthStatus> => {
  return apiRequest<HealthStatus>(ATLAS_HEALTH_PATH)
}

export { fetchAtlasHealth }
