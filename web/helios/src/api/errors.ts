import { ApiError } from '@/api/client'

const SERVER_ERROR_MESSAGE = 'The server could not complete the request. Try again later.'
const NETWORK_UNREACHABLE_MESSAGE =
  'Cannot reach the server. Check your connection and try again.'
const UNKNOWN_ERROR_MESSAGE = 'Something went wrong. Try again.'

const handleNetworkError = (error: unknown): string => {
  if (error instanceof ApiError) {
    return SERVER_ERROR_MESSAGE
  }
  if (error instanceof TypeError) {
    return NETWORK_UNREACHABLE_MESSAGE
  }
  return UNKNOWN_ERROR_MESSAGE
}

const getErrorDetail = (error: unknown): string | null => {
  if (error instanceof ApiError) {
    return error.detail
  }
  return null
}

const describeRequestError = (error: unknown): string => {
  const errorDetail = getErrorDetail(error)
  if (errorDetail !== null) {
    return errorDetail
  }
  return handleNetworkError(error)
}

export {
  describeRequestError,
  getErrorDetail,
  handleNetworkError,
  NETWORK_UNREACHABLE_MESSAGE,
  SERVER_ERROR_MESSAGE,
  UNKNOWN_ERROR_MESSAGE,
}
