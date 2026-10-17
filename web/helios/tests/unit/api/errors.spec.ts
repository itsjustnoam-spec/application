import { describe, expect, it } from 'vitest'

import { ApiError } from '@/api/client'
import {
  handleNetworkError,
  NETWORK_UNREACHABLE_MESSAGE,
  SERVER_ERROR_MESSAGE,
  UNKNOWN_ERROR_MESSAGE,
} from '@/api/errors'

describe('handleNetworkError', () => {
  it('returns the server error message when the API responds with an error status', () => {
    const message = handleNetworkError(new ApiError(500))

    expect(message).toBe(SERVER_ERROR_MESSAGE)
  })

  it('returns the unreachable message when the request never reaches the server', () => {
    const message = handleNetworkError(new TypeError('Failed to fetch'))

    expect(message).toBe(NETWORK_UNREACHABLE_MESSAGE)
  })

  it('returns the generic message when the error is not a network error', () => {
    const message = handleNetworkError(new Error('unexpected'))

    expect(message).toBe(UNKNOWN_ERROR_MESSAGE)
  })
})
