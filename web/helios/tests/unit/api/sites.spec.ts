import { describe, expect, it, vi } from 'vitest'

import { getSite } from '@/api/sites'
import { makeSite } from '../../mocks/factories/site'

describe('getSite', () => {
  it('returns the site from the sites path', async () => {
    const site = makeSite({ id: 4, name: 'Harbour Yard' })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(site), { status: 200 })))

    const result = await getSite(4)

    expect(result).toEqual(site)
  })
})
