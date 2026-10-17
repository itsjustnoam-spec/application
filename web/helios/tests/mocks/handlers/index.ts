import { atlasHealthHandler } from './health'
import {
  archiveAssetTypeHandler,
  createAssetTypeHandler,
  listAssetTypesHandler,
} from './asset-types'
import { archiveSiteHandler, createSiteHandler, listSitesHandler } from './sites'

export const handlers = [
  atlasHealthHandler,
  listSitesHandler,
  createSiteHandler,
  archiveSiteHandler,
  listAssetTypesHandler,
  createAssetTypeHandler,
  archiveAssetTypeHandler,
]
