import { http, HttpResponse } from 'msw'

import { makeSite } from '../factories/sites'

export const listSitesHandler = http.get('/api/atlas/sites', () => {
  return HttpResponse.json([makeSite()])
})

export const createSiteHandler = http.post('/api/atlas/sites', () => {
  return HttpResponse.json(makeSite(), { status: 201 })
})

export const updateSiteHandler = http.put('/api/atlas/sites/:siteId', () => {
  return HttpResponse.json(makeSite())
})

export const deleteSiteHandler = http.delete('/api/atlas/sites/:siteId', () => {
  return new HttpResponse(null, { status: 204 })
})
