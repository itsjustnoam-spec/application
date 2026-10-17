import { ApiError } from '@/api/client'
import { handleNetworkError } from '@/api/errors'

const HTTP_NOT_FOUND = 404
const HTTP_CONFLICT = 409
const HTTP_UNPROCESSABLE_ENTITY = 422

export const INVALID_VALUES_MESSAGE = 'Some values are invalid. Check the form and try again.'
export const ALREADY_DELETED_MESSAGE = 'This item was already deleted.'

export type WriteFailure =
  | { kind: 'name-taken' }
  | { kind: 'already-deleted' }
  | { kind: 'invalid-values' }
  | { kind: 'other'; message: string }

export const isNotFoundError = (error: unknown): boolean => {
  return error instanceof ApiError && error.status === HTTP_NOT_FOUND
}

export const classifyWriteError = (error: unknown): WriteFailure => {
  if (error instanceof ApiError && error.status === HTTP_CONFLICT) {
    return { kind: 'name-taken' }
  }
  if (isNotFoundError(error)) {
    return { kind: 'already-deleted' }
  }
  if (error instanceof ApiError && error.status === HTTP_UNPROCESSABLE_ENTITY) {
    return { kind: 'invalid-values' }
  }
  return { kind: 'other', message: handleNetworkError(error) }
}
