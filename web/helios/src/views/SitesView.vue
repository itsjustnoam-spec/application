<template>
  <v-container>
    <h1 class="flex items-center justify-center gap-2 text-center text-2xl font-semibold">
      Sites
      <EasyToolTip text="Physical locations where assets are installed." />
    </h1>
    <div class="my-4 flex justify-center">
      <v-btn color="primary" data-testid="create-site-button" @click="openCreateDialog">
        Add site
      </v-btn>
    </div>
    <v-progress-circular
      v-if="isLoading"
      class="mx-auto block"
      indeterminate
      data-testid="sites-loading"
    />
    <v-alert
      v-else-if="loadErrorMessage !== null"
      type="error"
      :text="loadErrorMessage"
      data-testid="sites-error"
    >
      <v-btn variant="text" data-testid="sites-retry-button" @click="loadSites">
        Retry
      </v-btn>
    </v-alert>
    <p v-else-if="sites.length === 0" class="text-center" data-testid="sites-empty">
      No sites yet.
    </p>
    <v-table v-else data-testid="sites-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Address</th>
          <th>Timezone</th>
          <th />
        </tr>
      </thead>
      <tbody>
        <tr v-for="site in sites" :key="site.id" :data-testid="`site-row-${site.id}`">
          <td>{{ site.name }}</td>
          <td>{{ site.address }}</td>
          <td>{{ site.timezone }}</td>
          <td class="text-right">
            <v-btn
              icon="mdi-pencil"
              variant="text"
              :aria-label="`Edit ${site.name}`"
              :data-testid="`edit-site-${site.id}`"
              @click="openEditDialog(site)"
            />
            <v-btn
              icon="mdi-delete"
              variant="text"
              :aria-label="`Delete ${site.name}`"
              :data-testid="`delete-site-${site.id}`"
              @click="openDeleteDialog(site)"
            />
          </td>
        </tr>
      </tbody>
    </v-table>

    <v-dialog v-model="isFormOpen" max-width="520">
      <SiteFormDialog
        :key="formKey"
        :site="selectedSite"
        @saved="onFormSaved"
        @cancel="closeForm"
        @already-deleted="onAlreadyDeleted"
      />
    </v-dialog>

    <v-dialog v-model="isDeleteOpen" max-width="420">
      <DeleteConfirmDialog
        title="Delete site"
        message="The site will be hidden from the list. Its name stays reserved."
        :is-loading="isDeleting"
        @confirm="confirmDelete"
        @cancel="closeDeleteDialog"
      />
    </v-dialog>

    <v-snackbar v-model="isSnackbarOpen" :text="snackbarMessage" data-testid="sites-snackbar" />
  </v-container>
</template>

<script setup lang="ts">
import { deleteSite, fetchSites } from '@/api/sites'
import { handleNetworkError } from '@/api/errors'
import EasyToolTip from '@/components/EasyToolTip.vue'
import DeleteConfirmDialog from '@/components/DeleteConfirmDialog.vue'
import SiteFormDialog from '@/components/SiteFormDialog.vue'
import type { Site } from '@/models/site'
import { ALREADY_DELETED_MESSAGE, isNotFoundError } from '@/utils/writeErrors'
import { onMounted, ref } from 'vue'

const sites = ref<Site[]>([])
const isLoading = ref<boolean>(true)
const loadErrorMessage = ref<string | null>(null)
const isFormOpen = ref<boolean>(false)
const formKey = ref<number>(0)
const selectedSite = ref<Site | null>(null)
const isDeleteOpen = ref<boolean>(false)
const siteToDelete = ref<Site | null>(null)
const isDeleting = ref<boolean>(false)
const isSnackbarOpen = ref<boolean>(false)
const snackbarMessage = ref<string>('')

const loadSites = async (): Promise<void> => {
  isLoading.value = true
  loadErrorMessage.value = null
  try {
    sites.value = await fetchSites()
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
  selectedSite.value = null
  formKey.value += 1
  isFormOpen.value = true
}

const openEditDialog = (site: Site): void => {
  selectedSite.value = site
  formKey.value += 1
  isFormOpen.value = true
}

const closeForm = (): void => {
  isFormOpen.value = false
}

const onFormSaved = (): void => {
  isFormOpen.value = false
  void loadSites()
}

const onAlreadyDeleted = (): void => {
  isFormOpen.value = false
  showSnackbar(ALREADY_DELETED_MESSAGE)
  void loadSites()
}

const openDeleteDialog = (site: Site): void => {
  siteToDelete.value = site
  isDeleteOpen.value = true
}

const closeDeleteDialog = (): void => {
  isDeleteOpen.value = false
}

const confirmDelete = async (): Promise<void> => {
  if (siteToDelete.value === null) {
    return
  }
  isDeleting.value = true
  try {
    await deleteSite(siteToDelete.value.id)
    isDeleteOpen.value = false
    await loadSites()
  } catch (error: unknown) {
    isDeleteOpen.value = false
    if (isNotFoundError(error)) {
      showSnackbar(ALREADY_DELETED_MESSAGE)
      await loadSites()
    } else {
      showSnackbar(handleNetworkError(error))
    }
  } finally {
    isDeleting.value = false
  }
}

onMounted(() => {
  void loadSites()
})
</script>
