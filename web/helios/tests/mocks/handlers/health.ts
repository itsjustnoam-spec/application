import { http, HttpResponse } from 'msw'

import { makeHealthStatus } from '../factories/health'

export const atlasHealthHandler = http.get('/api/atlas/health', () => {
  return HttpResponse.json(makeHealthStatus())
})
