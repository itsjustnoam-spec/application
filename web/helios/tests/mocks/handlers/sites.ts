import { http, HttpResponse } from 'msw'

import type { SiteInput } from '@/models/site'

import { makeSite, makeSitePage } from '../factories/site'

export const listSitesHandler = http.get('/api/atlas/sites', () => {
  return HttpResponse.json(makeSitePage())
})

export const createSiteHandler = http.post('/api/atlas/sites', async ({ request }) => {
  const body = (await request.json()) as SiteInput
  if (body.name.trim().length === 0) {
    return HttpResponse.json({ detail: 'Name is required.' }, { status: 422 })
  }
  return HttpResponse.json(makeSite({ name: body.name, address: body.address }), { status: 201 })
})

export const archiveSiteHandler = http.delete('/api/atlas/sites/:siteId', () => {
  return new HttpResponse(null, { status: 204 })
})
