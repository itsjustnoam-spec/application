import type { AssetInput } from '@/models/asset'

import { makeAsset, makeAssetPage } from '../../mocks/factories/asset'
import { makeAssetType, makeAssetTypePage } from '../../mocks/factories/asset-type'
import { makeSite, makeSitePage } from '../../mocks/factories/site'
import { expect, test } from '../fixtures'

const ASSETS_API_PATH = '/api/atlas/assets'
const NEW_ASSET_NAME = 'Valve Assembly'
const NEW_SERIAL_NUMBER = 'SN-9'

test.describe('Assets', () => {
  test('user creates an asset and sees it in the list', async ({ page, api }) => {
    const assets = [makeAsset({ name: 'Valve', serial_number: 'SN-0' })]
    await api.mock('GET', '/atlas/sites', makeSitePage([makeSite({ name: 'North Depot' })]))
    await api.mock('GET', '/atlas/asset-types', makeAssetTypePage([makeAssetType({ name: 'Pump' })]))
    await page.route((url) => url.pathname === ASSETS_API_PATH, async (route) => {
      if (route.request().method() === 'POST') {
        const input = route.request().postDataJSON() as AssetInput
        const createdAsset = makeAsset({
          id: 2,
          name: input.name,
          serial_number: input.serial_number,
          status: input.status,
          installation_date: input.installation_date,
          notes: input.notes,
        })
        assets.push(createdAsset)
        await route.fulfill({ status: 201, json: createdAsset })
        return
      }
      await route.fulfill({ status: 200, json: makeAssetPage(assets) })
    })
    await page.goto('/assets')

    await test.step('open the create dialog', async () => {
      await page.getByRole('button', { name: 'Add asset' }).click()
    })

    const dialog = page.getByRole('dialog')
    await test.step('fill the form', async () => {
      await dialog.getByLabel('Name', { exact: true }).fill(NEW_ASSET_NAME)
      await dialog.getByLabel('Serial number', { exact: true }).fill(NEW_SERIAL_NUMBER)
      await dialog.getByRole('combobox', { name: 'Site' }).click()
      await page.getByRole('option', { name: 'North Depot' }).click()
      await dialog.getByRole('combobox', { name: 'Asset type' }).click()
      await page.getByRole('option', { name: 'Pump' }).click()
      await dialog.getByRole('combobox', { name: 'Status' }).focus()
      await page.keyboard.press('ArrowDown')
      await page.getByRole('option', { name: 'Operational' }).click()
      await dialog.getByLabel('Installation date').fill('2026-01-01')
    })

    await test.step('save and check the list', async () => {
      await dialog.getByRole('button', { name: 'Save' }).click()

      await expect(
        page
          .getByRole('row')
          .filter({ hasText: NEW_ASSET_NAME })
          .filter({ hasText: NEW_SERIAL_NUMBER }),
      ).toBeVisible()
    })
  })
})
