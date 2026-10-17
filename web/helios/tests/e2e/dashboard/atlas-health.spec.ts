import { makeHealthStatus } from '../../mocks/factories/health'
import { expect, test } from '../fixtures'

test.describe('Dashboard', () => {
  test('user sees the atlas service status on the dashboard', async ({ page, api }) => {
    await api.mock('GET', '/atlas/health', makeHealthStatus({ status: 'ok' }))
    await page.goto('/dashboard')

    await expect(page.getByText('Atlas service: ok')).toBeVisible()
  })
})
