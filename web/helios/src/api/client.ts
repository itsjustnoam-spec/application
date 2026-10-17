const API_BASE_PATH = '/api'
const NO_CONTENT_STATUS = 204

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'

export interface ApiRequestOptions {
  method?: HttpMethod
  body?: unknown
}

export class ApiError extends Error {
  readonly status: number
  readonly detail: string | null

  constructor(status: number, detail: string | null = null) {
    super(`Request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

const readErrorDetail = async (response: Response): Promise<string | null> => {
  try {
    const body = (await response.json()) as { detail?: unknown }
    if (typeof body.detail === 'string') {
      return body.detail
    }
    if (Array.isArray(body.detail)) {
      return body.detail.map((item: { msg?: unknown }) => String(item.msg)).join('; ')
    }
    return null
  } catch {
    return null
  }
}

export const apiRequest = async <ResponseBody>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<ResponseBody> => {
  const hasBody = options.body !== undefined
  const response = await fetch(`${API_BASE_PATH}${path}`, {
    method: options.method ?? 'GET',
    headers: hasBody ? { 'Content-Type': 'application/json' } : undefined,
    body: hasBody ? JSON.stringify(options.body) : undefined,
  })
  if (!response.ok) {
    throw new ApiError(response.status, await readErrorDetail(response))
  }
  if (response.status === NO_CONTENT_STATUS) {
    return undefined as ResponseBody
  }
  return (await response.json()) as ResponseBody
}
