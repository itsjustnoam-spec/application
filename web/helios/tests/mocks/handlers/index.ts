import { archiveAssetHandler, createAssetHandler, listAssetsHandler } from './assets'
import { atlasHealthHandler } from './health'
import {
  archiveAssetTypeHandler,
  createAssetTypeHandler,
  listAssetTypesHandler,
} from './asset-types'
import { archiveSiteHandler, createSiteHandler, listSitesHandler } from './sites'

const handlers = [
  atlasHealthHandler,
  listSitesHandler,
  createSiteHandler,
  archiveSiteHandler,
  listAssetTypesHandler,
  createAssetTypeHandler,
  archiveAssetTypeHandler,
  listAssetsHandler,
  createAssetHandler,
  archiveAssetHandler,
]

export { handlers }
