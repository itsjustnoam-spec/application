import { test as base, expect } from '@playwright/test'

const API_PATH_PREFIX = '/api'

type ApiMocks = {
  mock: (method: string, path: string, json: unknown, status?: number) => Promise<void>
  mockError: (method: string, path: string, status: number, detail: string) => Promise<void>
}

export const test = base.extend<{ api: ApiMocks; failOnUnmockedRequests: void }>({
  failOnUnmockedRequests: [async ({ page }, use) => {
    const unmockedRequests: string[] = []
    await page.route((url) => url.pathname.startsWith(`${API_PATH_PREFIX}/`), async (route) => {
      unmockedRequests.push(`${route.request().method()} ${route.request().url()}`)
      await route.fulfill({ status: 501, json: { detail: 'Unmocked request in browser test' } })
    })
    await use()
    expect(unmockedRequests, 'every API request must be mocked').toEqual([])
  }, { auto: true }],

  api: async ({ page }, use) => {
    const register = async (method: string, path: string, status: number, json: unknown) => {
      await page.route((url) => url.pathname === `${API_PATH_PREFIX}${path}`, async (route) => {
        if (route.request().method() !== method) {
          await route.fallback()
          return
        }
        await route.fulfill({ status, json })
      })
    }
    await use({
      mock: (method, path, json, status = 200) => register(method, path, status, json),
      mockError: (method, path, status, detail) => register(method, path, status, { detail }),
    })
  },
})

export { expect }
