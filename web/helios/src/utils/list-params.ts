import type { ListParams } from '@/models/page'

const SEARCH_PARAM_NAME = 'q'
const SORT_PARAM_NAME = 'sort'
const DIRECTION_PARAM_NAME = 'direction'

const buildListQuery = (params: ListParams): string => {
  const query = new URLSearchParams({
    limit: String(params.limit),
    offset: String(params.offset),
  })
  if (params.query !== null && params.query.trim().length > 0) {
    query.set(SEARCH_PARAM_NAME, params.query.trim())
  }
  if (params.filters !== undefined) {
    for (const [key, value] of Object.entries(params.filters)) {
      if (value !== null && value !== '') {
        query.set(key, String(value))
      }
    }
  }
  if (params.sort !== undefined) {
    query.set(SORT_PARAM_NAME, params.sort)
  }
  if (params.direction !== undefined) {
    query.set(DIRECTION_PARAM_NAME, params.direction)
  }
  return query.toString()
}

export { buildListQuery }
