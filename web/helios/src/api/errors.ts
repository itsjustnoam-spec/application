import { ApiError } from '@/api/client'

export const SERVER_ERROR_MESSAGE = 'The server could not complete the request. Try again later.'
export const NETWORK_UNREACHABLE_MESSAGE =
  'Cannot reach the server. Check your connection and try again.'
export const UNKNOWN_ERROR_MESSAGE = 'Something went wrong. Try again.'

export const handleNetworkError = (error: unknown): string => {
  if (error instanceof ApiError) {
    return SERVER_ERROR_MESSAGE
  }
  if (error instanceof TypeError) {
    return NETWORK_UNREACHABLE_MESSAGE
  }
  return UNKNOWN_ERROR_MESSAGE
}
