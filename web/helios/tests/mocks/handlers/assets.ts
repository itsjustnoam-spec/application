import { http, HttpResponse } from 'msw'

import { ASSET_STATUSES, type AssetInput } from '@/models/asset'

import { makeAsset, makeAssetPage } from '../factories/asset'

const NAME_MAX_LENGTH = 100
const SERIAL_NUMBER_MAX_LENGTH = 100
const NOTES_MAX_LENGTH = 1000
const INSTALLATION_DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/

const validateAssetInput = (body: AssetInput): string[] => {
  const errors: string[] = []
  if (body.name.trim().length === 0 || body.name.length > NAME_MAX_LENGTH) {
    errors.push('name must be 1 to 100 characters')
  }
  if (
    body.serial_number.trim().length === 0 ||
    body.serial_number.length > SERIAL_NUMBER_MAX_LENGTH
  ) {
    errors.push('serial_number must be 1 to 100 characters')
  }
  if (!Number.isInteger(body.site_id) || !Number.isInteger(body.asset_type_id)) {
    errors.push('site_id and asset_type_id are required')
  }
  if (!ASSET_STATUSES.includes(body.status)) {
    errors.push('status is not a known value')
  }
  if (!INSTALLATION_DATE_PATTERN.test(body.installation_date)) {
    errors.push('installation_date must be a date')
  }
  if (body.notes !== null && body.notes.length > NOTES_MAX_LENGTH) {
    errors.push('notes must be at most 1000 characters')
  }
  return errors
}

const listAssetsHandler = http.get('/api/atlas/assets', () => {
  return HttpResponse.json(makeAssetPage())
})

const createAssetHandler = http.post('/api/atlas/assets', async ({ request }) => {
  const body = (await request.json()) as AssetInput
  const errors = validateAssetInput(body)
  if (errors.length > 0) {
    return HttpResponse.json({ detail: errors.join('; ') }, { status: 422 })
  }
  return HttpResponse.json(
    makeAsset({
      name: body.name,
      serial_number: body.serial_number,
      status: body.status,
      installation_date: body.installation_date,
      notes: body.notes,
    }),
    { status: 201 },
  )
})

const archiveAssetHandler = http.delete('/api/atlas/assets/:assetId', () => {
  return new HttpResponse(null, { status: 204 })
})

export { archiveAssetHandler, createAssetHandler, listAssetsHandler }
