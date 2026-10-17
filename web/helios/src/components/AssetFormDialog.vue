<template>
  <v-card>
    <v-card-title class="flex items-center justify-center gap-2 text-center">
      {{ dialogTitle }}
      <EasyToolTip text="Serial numbers are unique among active assets." />
    </v-card-title>
    <v-card-text>
      <v-text-field
        v-model="name"
        label="Name"
        :error-messages="nameErrorMessages"
        :counter="NAME_MAX_LENGTH"
        data-testid="asset-name-input"
      />
      <v-text-field
        v-model="serialNumber"
        label="Serial number"
        :error-messages="serialNumberErrorMessages"
        :counter="NAME_MAX_LENGTH"
        data-testid="asset-serial-number-input"
      />
      <ActiveEntitySelect
        v-model="siteId"
        label="Site"
        test-id="asset-site-select"
        :selected-option="selectedSiteOption"
        :error-messages="siteErrorMessages"
        :fetch-options="fetchActiveSiteOptions"
      />
      <ActiveEntitySelect
        v-model="assetTypeId"
        label="Asset type"
        test-id="asset-type-select"
        :selected-option="selectedAssetTypeOption"
        :error-messages="assetTypeErrorMessages"
        :fetch-options="fetchActiveAssetTypeOptions"
      />
      <v-select
        v-model="status"
        label="Status"
        :items="ASSET_STATUSES"
        :error-messages="statusErrorMessages"
        data-testid="asset-status-select"
      />
      <div class="flex items-center gap-2">
        <v-text-field
          v-model="installationDate"
          class="flex-1"
          label="Installation date"
          type="date"
          :error-messages="installationDateErrorMessages"
          data-testid="asset-installation-date-input"
        />
        <EasyToolTip text="The day the asset was installed. Its first inspection is due one asset type interval after this date." />
      </div>
      <v-textarea
        v-model="notes"
        label="Notes (optional)"
        rows="3"
        :counter="NOTES_MAX_LENGTH"
        :error-messages="notesErrorMessages"
        data-testid="asset-notes-input"
      />
      <v-alert
        v-if="errorMessage !== null"
        type="error"
        :text="errorMessage"
        data-testid="asset-form-error"
      />
    </v-card-text>
    <v-card-actions class="justify-end">
      <v-btn
        variant="text"
        data-testid="asset-form-cancel-button"
        @click="emit('cancel')"
      >
        Cancel
      </v-btn>
      <v-btn
        color="primary"
        :loading="isSaving"
        :disabled="isSaving"
        data-testid="asset-form-save-button"
        @click="submitForm"
      >
        Save
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import type { Asset } from '@/models/asset'

interface Props {
  asset: Asset | null
}

interface Emits {
  'saved': [Asset]
  'cancel': []
}

const NAME_MAX_LENGTH = 100
const NOTES_MAX_LENGTH = 1000
const REQUIRED_MESSAGE = 'This field is required.'
const INSTALLATION_DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/

const buildRequiredErrors = (hasSubmitAttempted: boolean, isValid: boolean): string[] =>
  hasSubmitAttempted && !isValid ? [REQUIRED_MESSAGE] : []
</script>

<script setup lang="ts">
import { computed, onBeforeMount, ref } from 'vue'

import { createAsset, updateAsset } from '@/api/assets'
import { describeRequestError } from '@/api/errors'
import ActiveEntitySelect from '@/components/ActiveEntitySelect.vue'
import EasyToolTip from '@/components/EasyToolTip.vue'
import { ASSET_STATUSES, type AssetInput, type AssetStatus } from '@/models/asset'
import type { SelectOption } from '@/models/select-option'
import { fetchActiveAssetTypeOptions, fetchActiveSiteOptions } from '@/utils/active-options'

const emit = defineEmits<Emits>()

const props = defineProps<Props>()

const name = ref<string>('')
const serialNumber = ref<string>('')
const siteId = ref<number | null>(null)
const assetTypeId = ref<number | null>(null)
const status = ref<AssetStatus | null>(null)
const installationDate = ref<string>('')
const notes = ref<string>('')
const hasSubmitAttempted = ref<boolean>(false)
const isSaving = ref<boolean>(false)
const errorMessage = ref<string | null>(null)

const selectedSiteOption = computed<SelectOption | null>(() =>
  props.asset === null ? null : { value: props.asset.site_id, title: props.asset.site_name },
)
const selectedAssetTypeOption = computed<SelectOption | null>(() =>
  props.asset === null
    ? null
    : { value: props.asset.asset_type_id, title: props.asset.asset_type_name },
)

const dialogTitle = computed<string>(() =>
  props.asset === null ? 'New asset' : 'Edit asset',
)

const isNameValid = computed<boolean>(
  () => name.value.trim().length > 0 && name.value.length <= NAME_MAX_LENGTH,
)
const isSerialNumberValid = computed<boolean>(
  () => serialNumber.value.trim().length > 0 && serialNumber.value.length <= NAME_MAX_LENGTH,
)
const isSiteValid = computed<boolean>(() => siteId.value !== null)
const isAssetTypeValid = computed<boolean>(() => assetTypeId.value !== null)
const isStatusValid = computed<boolean>(() => status.value !== null)
const isInstallationDateValid = computed<boolean>(
  () => INSTALLATION_DATE_PATTERN.test(installationDate.value),
)
const isNotesValid = computed<boolean>(() => notes.value.length <= NOTES_MAX_LENGTH)
const isFormValid = computed<boolean>(
  () =>
    isNameValid.value &&
    isSerialNumberValid.value &&
    isSiteValid.value &&
    isAssetTypeValid.value &&
    isStatusValid.value &&
    isInstallationDateValid.value &&
    isNotesValid.value,
)

const nameErrorMessages = computed<string[]>(() =>
  buildRequiredErrors(hasSubmitAttempted.value, isNameValid.value),
)
const serialNumberErrorMessages = computed<string[]>(() =>
  buildRequiredErrors(hasSubmitAttempted.value, isSerialNumberValid.value),
)
const siteErrorMessages = computed<string[]>(() =>
  buildRequiredErrors(hasSubmitAttempted.value, isSiteValid.value),
)
const assetTypeErrorMessages = computed<string[]>(() =>
  buildRequiredErrors(hasSubmitAttempted.value, isAssetTypeValid.value),
)
const statusErrorMessages = computed<string[]>(() =>
  buildRequiredErrors(hasSubmitAttempted.value, isStatusValid.value),
)
const installationDateErrorMessages = computed<string[]>(() =>
  buildRequiredErrors(hasSubmitAttempted.value, isInstallationDateValid.value),
)
const notesErrorMessages = computed<string[]>(() =>
  isNotesValid.value ? [] : [`Notes can be at most ${NOTES_MAX_LENGTH} characters.`],
)

const submitForm = async (): Promise<void> => {
  hasSubmitAttempted.value = true
  if (
    !isFormValid.value ||
    siteId.value === null ||
    assetTypeId.value === null ||
    status.value === null
  ) {
    return
  }

  const trimmedNotes = notes.value.trim()
  const input: AssetInput = {
    name: name.value.trim(),
    serial_number: serialNumber.value.trim(),
    site_id: siteId.value,
    asset_type_id: assetTypeId.value,
    status: status.value,
    installation_date: installationDate.value,
    notes: trimmedNotes.length === 0 ? null : trimmedNotes,
  }
  isSaving.value = true
  errorMessage.value = null
  try {
    if (props.asset === null) {
      emit('saved', await createAsset(input))
    } else {
      emit('saved', await updateAsset(props.asset.id, input))
    }
  } catch (error: unknown) {
    errorMessage.value = describeRequestError(error)
  } finally {
    isSaving.value = false
  }
}

function fillFormFromAsset() {
  if (props.asset === null) {
    return
  }
  name.value = props.asset.name
  serialNumber.value = props.asset.serial_number
  siteId.value = props.asset.site_id
  assetTypeId.value = props.asset.asset_type_id
  status.value = props.asset.status
  installationDate.value = props.asset.installation_date
  if (props.asset.notes !== null) {
    notes.value = props.asset.notes
  }
}

onBeforeMount(() => {
  fillFormFromAsset()
})
</script>
