import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { VSelect } from 'vuetify/components'

import AssetFormDialog from '@/components/AssetFormDialog.vue'
import type { AssetInput } from '@/models/asset'
import AssetsView from '@/views/AssetsView.vue'
import { makeAsset, makeAssetPage } from '../../mocks/factories/asset'
import { server } from '../../mocks/server'
import { mountWithPlugins } from '../../utils/mount'

const NEW_ASSET_NAME = 'Valve Assembly'
const NEW_SERIAL_NUMBER = 'SN-9'
const SITE_SELECT_TEST_ID = 'asset-site-select'
const SITE_NAME = 'North Depot'
const ASSET_TYPE_SELECT_TEST_ID = 'asset-type-select'
const ASSET_TYPE_NAME = 'Pump'
const STATUS_NAME = 'Operational'
const SERIAL_TAKEN_MESSAGE = 'An asset with this serial number already exists'

const mountAssetsViewWithDialogOpen = async () => {
  const wrapper = mountWithPlugins(AssetsView)
  await flushPromises()
  await wrapper.get('[data-testid="create-asset-button"]').trigger('click')
  return wrapper
}

const fillValidAssetForm = async (formDialog: VueWrapper) => {
  await formDialog.get('[data-testid="asset-name-input"] input').setValue(NEW_ASSET_NAME)
  await formDialog.get('[data-testid="asset-serial-number-input"] input').setValue(NEW_SERIAL_NUMBER)
  await formDialog.get('[data-testid="asset-installation-date-input"] input').setValue('2026-01-01')
  const siteInput = formDialog.get(`[data-testid="${SITE_SELECT_TEST_ID}"] input`)
  await siteInput.setValue(SITE_NAME)
  await siteInput.trigger('keydown', { key: 'ArrowDown' })
  await siteInput.trigger('keydown', { key: 'Enter' })
  const assetTypeInput = formDialog.get(`[data-testid="${ASSET_TYPE_SELECT_TEST_ID}"] input`)
  await assetTypeInput.setValue(ASSET_TYPE_NAME)
  await assetTypeInput.trigger('keydown', { key: 'ArrowDown' })
  await assetTypeInput.trigger('keydown', { key: 'Enter' })
  await formDialog.getComponent(VSelect).setValue(STATUS_NAME)
  await flushPromises()
}

describe('Assets: create and edit', () => {
  it('creates an asset and shows it in the list after saving', async () => {
    let assets = [makeAsset()]
    let submittedInput: AssetInput | null = null
    server.use(
      http.get('/api/atlas/assets', () => HttpResponse.json(makeAssetPage(assets))),
      http.post('/api/atlas/assets', async ({ request }) => {
        const body = (await request.json()) as AssetInput
        submittedInput = body
        const createdAsset = makeAsset({ id: 2, name: body.name, serial_number: body.serial_number })
        assets = [...assets, createdAsset]
        return HttpResponse.json(createdAsset, { status: 201 })
      }),
    )
    const wrapper = await mountAssetsViewWithDialogOpen()
    const formDialog = wrapper.findComponent(AssetFormDialog)

    await fillValidAssetForm(formDialog)
    await formDialog.get('[data-testid="asset-form-save-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.findComponent(AssetFormDialog).isVisible()).toBe(false)
    expect(wrapper.text()).toContain(NEW_ASSET_NAME)
    expect(submittedInput).toMatchObject({
      name: NEW_ASSET_NAME,
      serial_number: NEW_SERIAL_NUMBER,
      site_id: 1,
      asset_type_id: 1,
      status: 'Operational',
      installation_date: '2026-01-01',
    })
  })

  it('keeps the dialog open with the server message when the serial number is taken', async () => {
    server.use(
      http.post('/api/atlas/assets', () =>
        HttpResponse.json({ detail: SERIAL_TAKEN_MESSAGE }, { status: 409 }),
      ),
    )
    const wrapper = await mountAssetsViewWithDialogOpen()
    const formDialog = wrapper.findComponent(AssetFormDialog)
    await fillValidAssetForm(formDialog)

    await formDialog.get('[data-testid="asset-form-save-button"]').trigger('click')
    await flushPromises()

    const nameInput = formDialog.get('[data-testid="asset-name-input"] input').element as HTMLInputElement
    expect(wrapper.findComponent(AssetFormDialog).isVisible()).toBe(true)
    expect(nameInput.value).toBe(NEW_ASSET_NAME)
    expect(formDialog.get('[data-testid="asset-form-error"]').text()).toContain(SERIAL_TAKEN_MESSAGE)
  })

  it('disables the save button while the asset is being saved', async () => {
    let releaseSave: () => void = () => {}
    let saveRequestCount = 0
    server.use(
      http.post('/api/atlas/assets', async () => {
        saveRequestCount += 1
        await new Promise<void>((resolve) => {
          releaseSave = resolve
        })
        return HttpResponse.json(makeAsset({ id: 2, name: NEW_ASSET_NAME }), { status: 201 })
      }),
    )
    const wrapper = await mountAssetsViewWithDialogOpen()
    const formDialog = wrapper.findComponent(AssetFormDialog)
    await fillValidAssetForm(formDialog)
    const saveButton = formDialog.get('[data-testid="asset-form-save-button"]')

    await saveButton.trigger('click')
    await flushPromises()
    await saveButton.trigger('click')
    const isSaveDisabled = saveButton.attributes('disabled') !== undefined
    releaseSave()
    await flushPromises()

    expect(isSaveDisabled).toBe(true)
    expect(saveRequestCount).toBe(1)
  })
})
