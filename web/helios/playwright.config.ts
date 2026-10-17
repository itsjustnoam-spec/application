import { defineConfig, devices } from '@playwright/test'

const DEV_SERVER_PORT = 5173

export default defineConfig({
  testDir: 'tests/e2e',
  fullyParallel: true,
  forbidOnly: process.env.CI !== undefined,
  retries: process.env.CI !== undefined ? 2 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: `http://localhost:${DEV_SERVER_PORT}`,
    trace: 'on-first-retry',
    serviceWorkers: 'block',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run dev',
    url: `http://localhost:${DEV_SERVER_PORT}`,
    reuseExistingServer: process.env.CI === undefined,
  },
})
