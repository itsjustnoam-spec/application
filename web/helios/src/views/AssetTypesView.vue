<template>
  <div class="flex flex-col gap-4">
    <h2 class="flex items-center justify-center gap-2 text-center text-xl font-semibold">
      Asset types
      <EasyToolTip text="Kinds of assets, each with its own inspection interval." />
    </h2>
    <div class="flex items-center justify-between gap-4">
      <v-text-field
        class="flex-1"
        label="Search asset types"
        density="compact"
        hide-details
        clearable
        :model-value="searchText"
        data-testid="asset-type-search-input"
        @update:model-value="setSearchText"
      />
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        data-testid="create-asset-type-button"
        @click="openCreateDialog"
      >
        Add asset type
      </v-btn>
    </div>
    <v-alert
      v-if="errorMessage !== null"
      type="error"
      :text="errorMessage"
      data-testid="asset-types-error"
    >
      <v-btn
        variant="text"
        data-testid="retry-asset-types-button"
        @click="loadPage"
      >
        Retry
      </v-btn>
    </v-alert>
    <v-data-table-server
      :headers="ASSET_TYPE_TABLE_HEADERS"
      disable-sort
      :items="items"
      :items-length="total"
      :items-per-page="PAGE_SIZE"
      :page="page"
      :loading="isLoading"
      @update:page="setPage"
    >
      <template #item.actions="{ item }">
        <v-btn
          icon="mdi-pencil"
          variant="text"
          aria-label="Edit asset type"
          data-testid="edit-asset-type-button"
          @click="openEditDialog(item)"
        />
        <v-btn
          icon="mdi-archive"
          variant="text"
          aria-label="Archive asset type"
          data-testid="archive-asset-type-button"
          @click="openDeleteDialog(item)"
        />
      </template>
      <template #no-data>
        <p
          class="py-4 text-center"
          data-testid="asset-types-empty"
        >
          No asset types yet.
        </p>
      </template>
    </v-data-table-server>

    <v-dialog
      :model-value="isFormDialogOpen"
      :max-width="FORM_DIALOG_MAX_WIDTH"
      @update:model-value="closeFormDialog"
    >
      <AssetTypeFormDialog
        :key="formOpenCount"
        :asset-type="editingAssetType"
        @saved="onAssetTypeSaved"
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

const ASSET_TYPE_TABLE_HEADERS: DataTableHeader[] = [
  { title: 'Name', key: 'name' },
  { title: 'Category', key: 'category' },
  { title: 'Inspection interval (days)', key: 'inspection_interval_days' },
  { title: '', key: 'actions', sortable: false, align: 'end' },
]
const ARCHIVE_TITLE = 'Archive asset type'
const FORM_DIALOG_MAX_WIDTH = '35rem'
const CONFIRM_DIALOG_MAX_WIDTH = '26rem'
</script>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { deleteAssetType, listAssetTypes } from '@/api/asset-types'
import { describeRequestError } from '@/api/errors'
import AssetTypeFormDialog from '@/components/AssetTypeFormDialog.vue'
import ConfirmDeleteDialog from '@/components/ConfirmDeleteDialog.vue'
import EasyToolTip from '@/components/EasyToolTip.vue'
import type { AssetType } from '@/models/asset-type'
import { PAGE_SIZE, usePagedList } from '@/utils/use-paged-list'

const { items, total, page, searchText, isLoading, errorMessage, loadPage, setPage, setSearchText } =
  usePagedList(listAssetTypes)

const isFormDialogOpen = ref<boolean>(false)
const formOpenCount = ref<number>(0)
const editingAssetType = ref<AssetType | null>(null)
const isDeleteDialogOpen = ref<boolean>(false)
const assetTypeToDelete = ref<AssetType | null>(null)
const isArchiving = ref<boolean>(false)
const archiveErrorMessage = ref<string | null>(null)

const archiveMessage = computed<string>(() =>
  assetTypeToDelete.value === null
    ? ''
    : `Archive "${assetTypeToDelete.value.name}"? It will be hidden from lists.`,
)

const openFormDialog = (assetType: AssetType | null): void => {
  editingAssetType.value = assetType
  formOpenCount.value += 1
  isFormDialogOpen.value = true
}

const openCreateDialog = (): void => {
  openFormDialog(null)
}

const openEditDialog = (assetType: AssetType): void => {
  openFormDialog(assetType)
}

const closeFormDialog = (): void => {
  isFormDialogOpen.value = false
}

const onAssetTypeSaved = (): void => {
  closeFormDialog()
  loadPage()
}

const openDeleteDialog = (assetType: AssetType): void => {
  assetTypeToDelete.value = assetType
  archiveErrorMessage.value = null
  isDeleteDialogOpen.value = true
}

const closeDeleteDialog = (): void => {
  isDeleteDialogOpen.value = false
  assetTypeToDelete.value = null
}

const confirmArchive = async (): Promise<void> => {
  const assetType = assetTypeToDelete.value
  if (assetType !== null) {
    isArchiving.value = true
    archiveErrorMessage.value = null
    try {
      await deleteAssetType(assetType.id)
      closeDeleteDialog()
      await loadPage()
    } catch (error: unknown) {
      archiveErrorMessage.value = describeRequestError(error)
    } finally {
      isArchiving.value = false
    }
  }
}

onMounted(() => {
  loadPage()
})
</script>
