<template>
  <v-container>
    <h1 class="flex items-center justify-center gap-2 text-center text-2xl font-semibold">
      Asset Types
      <EasyToolTip text="Kinds of assets, with the inspection interval each kind needs." />
    </h1>
    <div class="my-4 flex justify-center">
      <v-btn
        color="primary"
        data-testid="create-asset-type-button"
        @click="openCreateDialog"
      >
        Add asset type
      </v-btn>
    </div>
    <v-progress-circular
      v-if="isLoading"
      class="mx-auto block"
      indeterminate
      data-testid="asset-types-loading"
    />
    <v-alert
      v-else-if="loadErrorMessage !== null"
      type="error"
      :text="loadErrorMessage"
      data-testid="asset-types-error"
    >
      <v-btn variant="text" data-testid="asset-types-retry-button" @click="loadAssetTypes">
        Retry
      </v-btn>
    </v-alert>
    <p
      v-else-if="assetTypes.length === 0"
      class="text-center"
      data-testid="asset-types-empty"
    >
      No asset types yet.
    </p>
    <v-table v-else data-testid="asset-types-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Category</th>
          <th>Inspection interval (days)</th>
          <th />
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="assetType in assetTypes"
          :key="assetType.id"
          :data-testid="`asset-type-row-${assetType.id}`"
        >
          <td>{{ assetType.name }}</td>
          <td>{{ assetType.category }}</td>
          <td>{{ assetType.inspection_interval_days }}</td>
          <td class="text-right">
            <v-btn
              icon="mdi-pencil"
              variant="text"
              :aria-label="`Edit ${assetType.name}`"
              :data-testid="`edit-asset-type-${assetType.id}`"
              @click="openEditDialog(assetType)"
            />
            <v-btn
              icon="mdi-delete"
              variant="text"
              :aria-label="`Delete ${assetType.name}`"
              :data-testid="`delete-asset-type-${assetType.id}`"
              @click="openDeleteDialog(assetType)"
            />
          </td>
        </tr>
      </tbody>
    </v-table>

    <v-dialog v-model="isFormOpen" max-width="520">
      <AssetTypeFormDialog
        :key="formKey"
        :asset-type="selectedAssetType"
        @saved="onFormSaved"
        @cancel="closeForm"
        @already-deleted="onAlreadyDeleted"
      />
    </v-dialog>

    <v-dialog v-model="isDeleteOpen" max-width="420">
      <DeleteConfirmDialog
        title="Delete asset type"
        message="The asset type will be hidden from the list. Its name stays reserved."
        :is-loading="isDeleting"
        @confirm="confirmDelete"
        @cancel="closeDeleteDialog"
      />
    </v-dialog>

    <v-snackbar
      v-model="isSnackbarOpen"
      :text="snackbarMessage"
      data-testid="asset-types-snackbar"
    />
  </v-container>
</template>

<script setup lang="ts">
import { deleteAssetType, fetchAssetTypes } from '@/api/assetTypes'
import { handleNetworkError } from '@/api/errors'
import AssetTypeFormDialog from '@/components/AssetTypeFormDialog.vue'
import DeleteConfirmDialog from '@/components/DeleteConfirmDialog.vue'
import EasyToolTip from '@/components/EasyToolTip.vue'
import type { AssetType } from '@/models/assetType'
import { ALREADY_DELETED_MESSAGE, isNotFoundError } from '@/utils/writeErrors'
import { onMounted, ref } from 'vue'

const assetTypes = ref<AssetType[]>([])
const isLoading = ref<boolean>(true)
const loadErrorMessage = ref<string | null>(null)
const isFormOpen = ref<boolean>(false)
const formKey = ref<number>(0)
const selectedAssetType = ref<AssetType | null>(null)
const isDeleteOpen = ref<boolean>(false)
const assetTypeToDelete = ref<AssetType | null>(null)
const isDeleting = ref<boolean>(false)
const isSnackbarOpen = ref<boolean>(false)
const snackbarMessage = ref<string>('')

const loadAssetTypes = async (): Promise<void> => {
  isLoading.value = true
  loadErrorMessage.value = null
  try {
    assetTypes.value = await fetchAssetTypes()
  } catch (error: unknown) {
    loadErrorMessage.value = handleNetworkError(error)
  } finally {
    isLoading.value = false
  }
}

const showSnackbar = (message: string): void => {
  snackbarMessage.value = message
  isSnackbarOpen.value = true
}

const openCreateDialog = (): void => {
  selectedAssetType.value = null
  formKey.value += 1
  isFormOpen.value = true
}

const openEditDialog = (assetType: AssetType): void => {
  selectedAssetType.value = assetType
  formKey.value += 1
  isFormOpen.value = true
}

const closeForm = (): void => {
  isFormOpen.value = false
}

const onFormSaved = (): void => {
  isFormOpen.value = false
  void loadAssetTypes()
}

const onAlreadyDeleted = (): void => {
  isFormOpen.value = false
  showSnackbar(ALREADY_DELETED_MESSAGE)
  void loadAssetTypes()
}

const openDeleteDialog = (assetType: AssetType): void => {
  assetTypeToDelete.value = assetType
  isDeleteOpen.value = true
}

const closeDeleteDialog = (): void => {
  isDeleteOpen.value = false
}

const confirmDelete = async (): Promise<void> => {
  if (assetTypeToDelete.value === null) {
    return
  }
  isDeleting.value = true
  try {
    await deleteAssetType(assetTypeToDelete.value.id)
    isDeleteOpen.value = false
    await loadAssetTypes()
  } catch (error: unknown) {
    isDeleteOpen.value = false
    if (isNotFoundError(error)) {
      showSnackbar(ALREADY_DELETED_MESSAGE)
      await loadAssetTypes()
    } else {
      showSnackbar(handleNetworkError(error))
    }
  } finally {
    isDeleting.value = false
  }
}

onMounted(() => {
  void loadAssetTypes()
})
</script>
