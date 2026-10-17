import { atlasHealthHandler } from './health'
import {
  createAssetTypeHandler,
  deleteAssetTypeHandler,
  listAssetTypesHandler,
  updateAssetTypeHandler,
} from './assetTypes'
import {
  createSiteHandler,
  deleteSiteHandler,
  listSitesHandler,
  updateSiteHandler,
} from './sites'

export const handlers = [
  atlasHealthHandler,
  listSitesHandler,
  createSiteHandler,
  updateSiteHandler,
  deleteSiteHandler,
  listAssetTypesHandler,
  createAssetTypeHandler,
  updateAssetTypeHandler,
  deleteAssetTypeHandler,
]
