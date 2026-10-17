<template>
  <div class="flex flex-col gap-4">
    <h2 class="flex items-center justify-center gap-2 text-center text-xl font-semibold">
      Assets
      <EasyToolTip text="Equipment at a site. Assets past their next inspection date are highlighted." />
    </h2>
    <div class="flex items-center justify-between gap-4">
      <v-text-field
        class="flex-1"
        label="Search by name or serial number"
        density="compact"
        hide-details
        clearable
        :model-value="searchText"
        data-testid="asset-search-input"
        @update:model-value="setSearchText"
      />
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        data-testid="create-asset-button"
        @click="openCreateDialog"
      >
        Add asset
      </v-btn>
    </div>
    <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
      <ActiveEntitySelect
        v-model="siteFilter"
        label="Site"
        test-id="asset-site-filter"
        :selected-option="null"
        :error-messages="[]"
        :fetch-options="fetchActiveSiteOptions"
      />
      <ActiveEntitySelect
        v-model="assetTypeFilter"
        label="Asset type"
        test-id="asset-type-filter"
        :selected-option="null"
        :error-messages="[]"
        :fetch-options="fetchActiveAssetTypeOptions"
      />
      <v-select
        v-model="statusFilter"
        label="Status"
        :items="ASSET_STATUSES"
        clearable
        data-testid="asset-status-filter"
      />
    </div>
    <v-alert
      v-if="errorMessage !== null"
      type="error"
      :text="errorMessage"
      data-testid="assets-error"
    >
      <v-btn
        variant="text"
        data-testid="retry-assets-button"
        @click="loadPage"
      >
        Retry
      </v-btn>
    </v-alert>
    <v-data-table-server
      :headers="ASSET_TABLE_HEADERS"
      :items="items"
      :items-length="total"
      :items-per-page="PAGE_SIZE"
      :page="page"
      :loading="isLoading"
      :sort-by="sortBy"
      :row-props="rowProps"
      @update:page="setPage"
      @update:sort-by="onSortUpdate"
    >
      <template #header.next_inspection_due>
        <span class="flex items-center gap-1">
          Next inspection (site time)
          <EasyToolTip text="Counted from the installation date, or the last inspection once inspections are recorded. Overdue when that date is before today in the site's timezone." />
        </span>
      </template>
      <template #item.next_inspection_due="{ item }">
        <span
          v-if="item.next_inspection_due === null"
          class="text-medium-emphasis"
        >
          No due date
        </span>
        <span
          v-else
          class="flex items-center gap-2"
        >
          {{ formatCalendarDate(item.next_inspection_due) }}
          <v-chip
            v-if="item.is_overdue"
            color="error"
            size="small"
            data-testid="asset-overdue-chip"
          >
            Overdue
          </v-chip>
        </span>
      </template>
      <template #item.actions="{ item }">
        <v-btn
          icon="mdi-pencil"
          variant="text"
          aria-label="Edit asset"
          data-testid="edit-asset-button"
          @click="openEditDialog(item)"
        />
        <v-btn
          icon="mdi-archive"
          variant="text"
          aria-label="Archive asset"
          data-testid="archive-asset-button"
          @click="openDeleteDialog(item)"
        />
      </template>
      <template #no-data>
        <p
          class="py-4 text-center"
          data-testid="assets-empty"
        >
          No assets match these filters.
        </p>
      </template>
    </v-data-table-server>

    <v-dialog
      :model-value="isFormDialogOpen"
      :max-width="FORM_DIALOG_MAX_WIDTH"
      @update:model-value="closeFormDialog"
    >
      <AssetFormDialog
        :key="formOpenCount"
        :asset="editingAsset"
        @saved="onAssetSaved"
        @cancel="closeFormDialog"
      />
    </v-dialog>

    <v-dialog
      :model-value="isDeleteDialogOpen"
      :max-width="CONFIRM_DIALOG_MAX_WIDTH"
      @update:model-value="closeDeleteDialog"
    >
      <ConfirmDeleteDialog
        :title="ARCHIVE_TITLE"
        :message="archiveMessage"
        :is-loading="isArchiving"
        :error-message="archiveErrorMessage"
        @confirm="confirmArchive"
        @cancel="closeDeleteDialog"
      />
    </v-dialog>
  </div>
</template>

<script lang="ts">
import type { DataTableHeader } from 'vuetify'

interface AssetSortItem {
  key: string
  order: 'asc' | 'desc' | boolean
}

const ASSET_TABLE_HEADERS: DataTableHeader[] = [
  { title: 'Name', key: 'name' },
  { title: 'Serial number', key: 'serial_number', sortable: false },
  { title: 'Site', key: 'site_name', sortable: false },
  { title: 'Asset type', key: 'asset_type_name', sortable: false },
  { title: 'Status', key: 'status', sortable: false },
  { title: 'Next inspection (site time)', key: 'next_inspection_due' },
  { title: '', key: 'actions', sortable: false, align: 'end' },
]
const OVERDUE_ROW_CLASS = 'asset-row-overdue'
const ARCHIVE_TITLE = 'Archive asset'
const FORM_DIALOG_MAX_WIDTH = '40rem'
const CONFIRM_DIALOG_MAX_WIDTH = '26rem'
const DEFAULT_SORT_KEY = 'name'
const DEFAULT_SORT_DIRECTION = 'asc'

export type { AssetSortItem }
</script>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { deleteAsset, listAssets } from '@/api/assets'
import { getErrorDetail, handleNetworkError } from '@/api/errors'
import ActiveEntitySelect from '@/components/ActiveEntitySelect.vue'
import AssetFormDialog from '@/components/AssetFormDialog.vue'
import ConfirmDeleteDialog from '@/components/ConfirmDeleteDialog.vue'
import EasyToolTip from '@/components/EasyToolTip.vue'
import { ASSET_STATUSES, type Asset, type AssetStatus } from '@/models/asset'
import type { ListFilterValue } from '@/models/page'
import { fetchActiveAssetTypeOptions, fetchActiveSiteOptions } from '@/utils/active-options'
import { formatCalendarDate } from '@/utils/format-calendar-date'
import { PAGE_SIZE, usePagedList } from '@/utils/use-paged-list'

const {
  items,
  total,
  page,
  searchText,
  isLoading,
  errorMessage,
  loadPage,
  setPage,
  setSearchText,
  setFilters,
  setSort,
} = usePagedList(listAssets)

const siteFilter = ref<number | null>(null)
const assetTypeFilter = ref<number | null>(null)
const statusFilter = ref<AssetStatus | null>(null)
const sortBy = ref<AssetSortItem[]>([{ key: DEFAULT_SORT_KEY, order: DEFAULT_SORT_DIRECTION }])

const isFormDialogOpen = ref<boolean>(false)
const formOpenCount = ref<number>(0)
const editingAsset = ref<Asset | null>(null)
const isDeleteDialogOpen = ref<boolean>(false)
const assetToDelete = ref<Asset | null>(null)
const isArchiving = ref<boolean>(false)
const archiveErrorMessage = ref<string | null>(null)

const archiveMessage = computed<string>(() =>
  assetToDelete.value === null
    ? ''
    : `Archive "${assetToDelete.value.name}"? It will be hidden from lists.`,
)

const rowProps = ({ item }: { item: Asset }) => ({
  class: item.is_overdue ? OVERDUE_ROW_CLASS : undefined,
  'data-testid': 'asset-row',
})

const applyFilters = (): void => {
  const filters: Record<string, ListFilterValue> = {
    site_id: siteFilter.value,
    asset_type_id: assetTypeFilter.value,
    status: statusFilter.value,
  }
  setFilters(filters)
}

const onSortUpdate = (nextSort: AssetSortItem[]): void => {
  sortBy.value = nextSort
  const [first] = nextSort
  if (first === undefined) {
    sortBy.value = [{ key: DEFAULT_SORT_KEY, order: DEFAULT_SORT_DIRECTION }]
    setSort(DEFAULT_SORT_KEY, DEFAULT_SORT_DIRECTION)
    return
  }
  setSort(first.key, first.order === 'desc' ? 'desc' : 'asc')
}

const openFormDialog = (asset: Asset | null): void => {
  editingAsset.value = asset
  formOpenCount.value += 1
  isFormDialogOpen.value = true
}

const openCreateDialog = (): void => {
  openFormDialog(null)
}

const openEditDialog = (asset: Asset): void => {
  openFormDialog(asset)
}

const closeFormDialog = (): void => {
  isFormDialogOpen.value = false
}

const onAssetSaved = (): void => {
  closeFormDialog()
  void loadPage()
}

const openDeleteDialog = (asset: Asset): void => {
  assetToDelete.value = asset
  archiveErrorMessage.value = null
  isDeleteDialogOpen.value = true
}

const closeDeleteDialog = (): void => {
  isDeleteDialogOpen.value = false
  assetToDelete.value = null
}

const confirmArchive = async (): Promise<void> => {
  const asset = assetToDelete.value
  if (asset !== null) {
    isArchiving.value = true
    archiveErrorMessage.value = null
    try {
      await deleteAsset(asset.id)
      closeDeleteDialog()
      await loadPage()
    } catch (error: unknown) {
      archiveErrorMessage.value = getErrorDetail(error) ?? handleNetworkError(error)
    } finally {
      isArchiving.value = false
    }
  }
}

watch([siteFilter, assetTypeFilter, statusFilter], applyFilters)

onMounted(() => {
  void loadPage()
})
</script>

<style scoped>
.asset-row-overdue {
  background-color: rgb(var(--v-theme-error) / 0.08);
}
</style>
