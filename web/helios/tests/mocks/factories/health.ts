import type { HealthStatus } from '@/models/health'

const makeHealthStatus = (overrides: Partial<HealthStatus> = {}): HealthStatus => {
  return {
    status: 'ok',
    ...overrides,
  }
}

export { makeHealthStatus }
