const API_BASE_PATH = '/api'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number) {
    super(`Request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
  }
}

export const apiRequest = async <ResponseBody>(path: string): Promise<ResponseBody> => {
  const response = await fetch(`${API_BASE_PATH}${path}`)
  if (!response.ok) {
    throw new ApiError(response.status)
  }
  return (await response.json()) as ResponseBody
}
