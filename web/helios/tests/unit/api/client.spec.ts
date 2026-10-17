import { describe, expect, it, vi } from 'vitest'

import { apiRequest, apiRequestWithoutContent, ApiError } from '@/api/client'

const SITE_NAME_TAKEN_DETAIL = 'A site with this name already exists'

describe('apiRequest', () => {
  it('sends the method and a JSON body when posting a payload', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{"id":1}', { status: 201 }))
    vi.stubGlobal('fetch', fetchMock)

    await apiRequest('/atlas/sites', { method: 'POST', body: { name: 'HQ' } })

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/atlas/sites',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ name: 'HQ' }),
        headers: { 'Content-Type': 'application/json' },
      }),
    )
  })

  it('throws an ApiError carrying the backend detail when the response is an error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: SITE_NAME_TAKEN_DETAIL }), { status: 409 }),
      ),
    )

    const request = apiRequest('/atlas/sites', { method: 'POST', body: { name: 'HQ' } })

    await expect(request).rejects.toMatchObject({
      status: 409,
      detail: SITE_NAME_TAKEN_DETAIL,
    })
  })

  it('joins the validation messages when the backend returns a list of errors', async () => {
    const validationBody = {
      detail: [
        { msg: 'Value error, Mars/Olympus is not a valid IANA timezone.' },
        { msg: 'String should have at least 1 character' },
      ],
    }
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify(validationBody), { status: 422 })),
    )

    const request = apiRequest('/atlas/sites', { method: 'POST', body: {} })

    await expect(request).rejects.toBeInstanceOf(ApiError)
    await expect(request).rejects.toMatchObject({
      detail:
        'Value error, Mars/Olympus is not a valid IANA timezone.; String should have at least 1 character',
    })
  })

  it('resolves with no value when the backend responds with no content', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })))

    await expect(
      apiRequestWithoutContent('/atlas/sites/1', { method: 'DELETE' }),
    ).resolves.toBeUndefined()
  })

  it('returns a null detail when the error body has no detail field', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 500 })))

    const request = apiRequest('/atlas/sites')

    await expect(request).rejects.toMatchObject({ status: 500, detail: null })
  })

  it('returns a null detail when the error body is not JSON', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('gateway down', { status: 502 })))

    const request = apiRequest('/atlas/sites')

    await expect(request).rejects.toMatchObject({ status: 502, detail: null })
  })
})
