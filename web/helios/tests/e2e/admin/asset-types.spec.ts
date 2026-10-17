import type { AssetTypeInput } from '@/models/asset-type'

import { makeAssetType, makeAssetTypePage } from '../../mocks/factories/asset-type'
import { expect, test } from '../fixtures'

const ASSET_TYPES_API_PATH = '/api/atlas/asset-types'

test.describe('Admin asset types', () => {
  test('user creates an asset type and sees it in the list', async ({ page }) => {
    const assetTypes = [makeAssetType({ name: 'Valve' })]
    await page.route((url) => url.pathname === ASSET_TYPES_API_PATH, async (route) => {
      if (route.request().method() === 'POST') {
        const input = route.request().postDataJSON() as AssetTypeInput
        const createdAssetType = makeAssetType({
          id: 2,
          name: input.name,
          category: input.category,
          inspection_interval_days: input.inspection_interval_days,
        })
        assetTypes.push(createdAssetType)
        await route.fulfill({ status: 201, json: createdAssetType })
        return
      }
      await route.fulfill({ status: 200, json: makeAssetTypePage(assetTypes) })
    })
    await page.goto('/admin/asset-types')

    await page.getByRole('button', { name: 'Add asset type' }).click()
    await page.getByLabel('Name').fill('Pump')
    await page.getByRole('combobox', { name: 'Category' }).focus()
    await page.keyboard.press('ArrowDown')
    await page.getByRole('option', { name: 'HVAC' }).click()
    await page.getByLabel('Inspection interval (days)').fill('30')
    await page.getByRole('button', { name: 'Save' }).click()

    await expect(page.getByRole('row').filter({ hasText: 'Pump' })).toBeVisible()
  })
})
