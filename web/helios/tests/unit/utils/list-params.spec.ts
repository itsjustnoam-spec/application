import { describe, expect, it } from 'vitest'

import { buildListQuery } from '@/utils/list-params'

describe('buildListQuery', () => {
  it('includes the trimmed search text as the q parameter', () => {
    const query = buildListQuery({ limit: 20, offset: 0, query: '  pump  ' })

    expect(query).toBe('limit=20&offset=0&q=pump')
  })

  it('omits the q parameter when the search text is blank', () => {
    const query = buildListQuery({ limit: 20, offset: 40, query: '   ' })

    expect(query).toBe('limit=20&offset=40')
  })

  it('includes filters, sort and direction in the list query', () => {
    const query = buildListQuery({
      limit: 20,
      offset: 0,
      query: null,
      filters: { site_id: 3, status: 'Retired' },
      sort: 'next_inspection_due',
      direction: 'desc',
    })

    expect(query).toBe(
      'limit=20&offset=0&site_id=3&status=Retired&sort=next_inspection_due&direction=desc',
    )
  })

  it('leaves out filters that are empty', () => {
    const query = buildListQuery({
      limit: 20,
      offset: 0,
      query: null,
      filters: { site_id: null, status: '' },
    })

    expect(query).toBe('limit=20&offset=0')
  })
})
