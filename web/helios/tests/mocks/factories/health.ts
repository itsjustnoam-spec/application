import type { HealthStatus } from '@/models/health'

export const makeHealthStatus = (overrides: Partial<HealthStatus> = {}): HealthStatus => {
  return {
    status: 'ok',
    ...overrides,
  }
}
