import type { SiteInput } from '@/models/site'

import { makeSite, makeSitePage } from '../../mocks/factories/site'
import { expect, test } from '../fixtures'

const SITES_API_PATH = '/api/atlas/sites'
const SITE_NAME_TAKEN_DETAIL = 'A site with this name already exists'

test.describe('Admin sites', () => {
  test('user creates a site and sees it in the list', async ({ page }) => {
    const sites = [makeSite({ name: 'North Depot' })]
    await page.route((url) => url.pathname === SITES_API_PATH, async (route) => {
      if (route.request().method() === 'POST') {
        const input = route.request().postDataJSON() as SiteInput
        const createdSite = makeSite({ id: 2, name: input.name, address: input.address })
        sites.push(createdSite)
        await route.fulfill({ status: 201, json: createdSite })
        return
      }
      await route.fulfill({ status: 200, json: makeSitePage(sites) })
    })
    await page.goto('/admin/sites')

    await page.getByRole('button', { name: 'Add site' }).click()
    await page.getByLabel('Name').fill('Harbour Yard')
    await page.getByLabel('Address').fill('4 Quay Street')
    await page.getByLabel('Timezone').fill('Europe/Berlin')
    await page.getByRole('option', { name: 'Europe/Berlin' }).click()
    await page.getByRole('button', { name: 'Save' }).click()

    await expect(page.getByRole('row').filter({ hasText: 'Harbour Yard' })).toBeVisible()
  })

  test('user sees the duplicate name error in the site dialog', async ({ page }) => {
    await page.route((url) => url.pathname === SITES_API_PATH, async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({ status: 409, json: { detail: SITE_NAME_TAKEN_DETAIL } })
        return
      }
      await route.fulfill({ status: 200, json: makeSitePage([makeSite()]) })
    })
    await page.goto('/admin/sites')

    await page.getByRole('button', { name: 'Add site' }).click()
    await page.getByLabel('Name').fill('North Depot')
    await page.getByLabel('Address').fill('1 Main Street')
    await page.getByLabel('Timezone').fill('Europe/Berlin')
    await page.getByRole('option', { name: 'Europe/Berlin' }).click()
    await page.getByRole('button', { name: 'Save' }).click()

    await expect(page.getByText(SITE_NAME_TAKEN_DETAIL)).toBeVisible()
    await expect(page.getByRole('button', { name: 'Save' })).toBeVisible()
  })

  test('user archives a site after confirming and it leaves the list', async ({ page }) => {
    const sites = [makeSite({ name: 'North Depot' })]
    await page.route((url) => url.pathname === SITES_API_PATH, async (route) => {
      await route.fulfill({ status: 200, json: makeSitePage(sites) })
    })
    await page.route(
      (url) => url.pathname.startsWith(`${SITES_API_PATH}/`),
      async (route) => {
        const archivedSiteId = Number(new URL(route.request().url()).pathname.split('/').pop())
        const remainingSites = sites.filter((site) => site.id !== archivedSiteId)
        sites.length = 0
        sites.push(...remainingSites)
        await route.fulfill({ status: 204 })
      },
    )
    await page.goto('/admin/sites')

    await page.getByRole('button', { name: 'Archive site' }).click()
    await page.getByRole('button', { name: 'Archive', exact: true }).click()

    await expect(page.getByRole('row').filter({ hasText: 'North Depot' })).toHaveCount(0)
  })
})
