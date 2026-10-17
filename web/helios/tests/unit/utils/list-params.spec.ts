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
})
