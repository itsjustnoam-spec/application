<template>
  <div class="flex flex-col gap-4">
    <h2 class="flex items-center justify-center gap-2 text-center text-xl font-semibold">
      Sites
      <EasyToolTip text="Physical locations where assets are installed." />
    </h2>
    <div class="flex items-center justify-between gap-4">
      <v-text-field
        class="flex-1"
        label="Search sites"
        density="compact"
        hide-details
        clearable
        :model-value="searchText"
        data-testid="site-search-input"
        @update:model-value="setSearchText"
      />
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        data-testid="create-site-button"
        @click="openCreateDialog"
      >
        Add site
      </v-btn>
    </div>
    <v-alert
      v-if="errorMessage !== null"
      type="error"
      :text="errorMessage"
      data-testid="sites-error"
    >
      <v-btn
        variant="text"
        data-testid="retry-sites-button"
        @click="loadPage"
      >
        Retry
      </v-btn>
    </v-alert>
    <v-data-table-server
      :headers="SITE_TABLE_HEADERS"
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
          aria-label="Edit site"
          data-testid="edit-site-button"
          @click="openEditDialog(item)"
        />
        <v-btn
          icon="mdi-archive"
          variant="text"
          aria-label="Archive site"
          data-testid="archive-site-button"
          @click="openDeleteDialog(item)"
        />
      </template>
      <template #no-data>
        <p
          class="py-4 text-center"
          data-testid="sites-empty"
        >
          No sites yet.
        </p>
      </template>
    </v-data-table-server>

    <v-dialog
      :model-value="isFormDialogOpen"
      :max-width="FORM_DIALOG_MAX_WIDTH"
      @update:model-value="closeFormDialog"
    >
      <SiteFormDialog
        :key="formOpenCount"
        :site="editingSite"
        @saved="onSiteSaved"
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

const SITE_TABLE_HEADERS: DataTableHeader[] = [
  { title: 'Name', key: 'name' },
  { title: 'Address', key: 'address' },
  { title: 'Timezone', key: 'timezone' },
  { title: '', key: 'actions', sortable: false, align: 'end' },
]
const ARCHIVE_TITLE = 'Archive site'
const FORM_DIALOG_MAX_WIDTH = '35rem'
const CONFIRM_DIALOG_MAX_WIDTH = '26rem'
</script>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { deleteSite, listSites } from '@/api/sites'
import { describeRequestError } from '@/api/errors'
import ConfirmDeleteDialog from '@/components/ConfirmDeleteDialog.vue'
import EasyToolTip from '@/components/EasyToolTip.vue'
import SiteFormDialog from '@/components/SiteFormDialog.vue'
import type { Site } from '@/models/site'
import { PAGE_SIZE, usePagedList } from '@/utils/use-paged-list'

const { items, total, page, searchText, isLoading, errorMessage, loadPage, setPage, setSearchText } =
  usePagedList(listSites)

const isFormDialogOpen = ref<boolean>(false)
const formOpenCount = ref<number>(0)
const editingSite = ref<Site | null>(null)
const isDeleteDialogOpen = ref<boolean>(false)
const siteToDelete = ref<Site | null>(null)
const isArchiving = ref<boolean>(false)
const archiveErrorMessage = ref<string | null>(null)

const archiveMessage = computed<string>(() =>
  siteToDelete.value === null ? '' : `Archive "${siteToDelete.value.name}"? It will be hidden from lists.`,
)

const openFormDialog = (site: Site | null): void => {
  editingSite.value = site
  formOpenCount.value += 1
  isFormDialogOpen.value = true
}

const openCreateDialog = (): void => {
  openFormDialog(null)
}

const openEditDialog = (site: Site): void => {
  openFormDialog(site)
}

const closeFormDialog = (): void => {
  isFormDialogOpen.value = false
}

const onSiteSaved = (): void => {
  closeFormDialog()
  loadPage()
}

const openDeleteDialog = (site: Site): void => {
  siteToDelete.value = site
  archiveErrorMessage.value = null
  isDeleteDialogOpen.value = true
}

const closeDeleteDialog = (): void => {
  isDeleteDialogOpen.value = false
  siteToDelete.value = null
}

const confirmArchive = async (): Promise<void> => {
  const site = siteToDelete.value
  if (site !== null) {
    isArchiving.value = true
    archiveErrorMessage.value = null
    try {
      await deleteSite(site.id)
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
