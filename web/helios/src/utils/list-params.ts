import type { ListParams } from '@/models/page'

const SEARCH_PARAM_NAME = 'q'

const buildListQuery = (params: ListParams): string => {
  const query = new URLSearchParams({
    limit: String(params.limit),
    offset: String(params.offset),
  })
  if (params.query !== null && params.query.trim().length > 0) {
    query.set(SEARCH_PARAM_NAME, params.query.trim())
  }
  return query.toString()
}

export { buildListQuery }
