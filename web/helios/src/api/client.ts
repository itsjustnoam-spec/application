const API_BASE_PATH = '/api'
const JSON_CONTENT_TYPE = 'application/json'
const NO_CONTENT_STATUS = 204

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'

export interface ApiRequestOptions {
  method?: HttpMethod
  body?: unknown
}

export class ApiError extends Error {
  readonly status: number

  constructor(status: number) {
    super(`Request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
  }
}

export const apiRequest = async <ResponseBody>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<ResponseBody> => {
  const hasBody = options.body !== undefined
  const response = await fetch(`${API_BASE_PATH}${path}`, {
    method: options.method ?? 'GET',
    headers: hasBody ? { 'Content-Type': JSON_CONTENT_TYPE } : undefined,
    body: hasBody ? JSON.stringify(options.body) : undefined,
  })
  if (!response.ok) {
    throw new ApiError(response.status)
  }
  if (response.status === NO_CONTENT_STATUS) {
    return undefined as ResponseBody
  }
  return (await response.json()) as ResponseBody
}
