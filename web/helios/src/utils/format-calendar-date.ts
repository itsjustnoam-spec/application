const CALENDAR_DATE_FORMAT = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeZone: 'UTC',
})

// The API sends calendar dates as YYYY-MM-DD, which must not shift with the viewer's timezone.
const formatCalendarDate = (isoDate: string): string => {
  return CALENDAR_DATE_FORMAT.format(new Date(`${isoDate}T00:00:00Z`))
}

export { formatCalendarDate }
