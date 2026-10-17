import { afterEach, describe, expect, it, vi } from 'vitest'

const CALENDAR_DATE = '2026-10-17'
const EAST_OF_UTC_TIMEZONE = 'Pacific/Kiritimati'
const WEST_OF_UTC_TIMEZONE = 'America/Los_Angeles'

const formatDateInTimezone = async (timezone: string): Promise<string> => {
  vi.stubEnv('TZ', timezone)
  vi.resetModules()
  const { formatCalendarDate } = await import('@/utils/format-calendar-date')
  return formatCalendarDate(CALENDAR_DATE)
}

afterEach(() => {
  vi.unstubAllEnvs()
})

describe('formatCalendarDate', () => {
  it('shows the calendar day unchanged whatever the viewer timezone', async () => {
    const formattedEast = await formatDateInTimezone(EAST_OF_UTC_TIMEZONE)
    const formattedWest = await formatDateInTimezone(WEST_OF_UTC_TIMEZONE)

    expect(formattedEast).toBe(formattedWest)
    expect(formattedEast).toContain('17')
    expect(formattedEast).not.toContain('16')
  })
})
