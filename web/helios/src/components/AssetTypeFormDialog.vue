<template>
  <v-card>
    <v-card-title class="flex items-center justify-center gap-2 text-center">
      {{ dialogTitle }}
      <EasyToolTip text="An asset type sets how often each asset of that kind must be inspected." />
    </v-card-title>
    <v-card-text>
      <v-text-field
        v-model="name"
        label="Name"
        :error-messages="nameErrorMessages"
        :counter="NAME_MAX_LENGTH"
        data-testid="asset-type-name-input"
      />
      <v-select
        v-model="category"
        label="Category"
        :items="ASSET_CATEGORIES"
        :error-messages="categoryErrorMessages"
        data-testid="asset-type-category-select"
      />
      <div class="flex items-center gap-2">
        <EasyToolTip text="Whole days between inspections, from 1 to 3650." />
      </div>
      <v-text-field
        v-model="intervalText"
        label="Inspection interval (days)"
        type="number"
        :error-messages="intervalErrorMessages"
        data-testid="asset-type-interval-input"
      />
      <v-alert
        v-if="errorMessage !== null"
        type="error"
        :text="errorMessage"
        data-testid="asset-type-form-error"
      />
    </v-card-text>
    <v-card-actions class="justify-end">
      <v-btn
        variant="text"
        data-testid="asset-type-form-cancel-button"
        @click="emit('cancel')"
      >
        Cancel
      </v-btn>
      <v-btn
        color="primary"
        :loading="isSaving"
        :disabled="isSaving"
        data-testid="asset-type-form-save-button"
        @click="submitForm"
      >
        Save
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import type { AssetType } from '@/models/asset-type'

interface AssetTypeFormProps {
  assetType: AssetType | null
}

interface AssetTypeFormEmits {
  'saved': [AssetType]
  'cancel': []
}

const NAME_MAX_LENGTH = 100
const INSPECTION_INTERVAL_MIN_DAYS = 1
const INSPECTION_INTERVAL_MAX_DAYS = 3650
const REQUIRED_MESSAGE = 'This field is required.'
const INTERVAL_RANGE_MESSAGE = 'Enter a whole number of days from 1 to 3650.'

export type { AssetTypeFormEmits, AssetTypeFormProps }
</script>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { createAssetType, updateAssetType } from '@/api/asset-types'
import { getErrorDetail, handleNetworkError } from '@/api/errors'
import EasyToolTip from '@/components/EasyToolTip.vue'
import { ASSET_CATEGORIES, type AssetCategory, type AssetTypeInput } from '@/models/asset-type'

const emit = defineEmits<AssetTypeFormEmits>()

const props = defineProps<AssetTypeFormProps>()

const name = ref<string>(props.assetType?.name ?? '')
const category = ref<AssetCategory | null>(props.assetType?.category ?? null)
const intervalText = ref<string>(
  props.assetType === null ? '' : String(props.assetType.inspection_interval_days),
)
const hasSubmitAttempted = ref<boolean>(false)
const isSaving = ref<boolean>(false)
const errorMessage = ref<string | null>(null)

const dialogTitle = computed<string>(() =>
  props.assetType === null ? 'New asset type' : 'Edit asset type',
)

const isNameValid = computed<boolean>(
  () => name.value.trim().length > 0 && name.value.length <= NAME_MAX_LENGTH,
)
const isIntervalValid = computed<boolean>(() => {
  const days = Number(intervalText.value)
  return (
    Number.isInteger(days) &&
    days >= INSPECTION_INTERVAL_MIN_DAYS &&
    days <= INSPECTION_INTERVAL_MAX_DAYS
  )
})
const isCategoryValid = computed<boolean>(() => category.value !== null)
const isFormValid = computed<boolean>(
  () => isNameValid.value && isIntervalValid.value && isCategoryValid.value,
)

const nameErrorMessages = computed<string[]>(() =>
  hasSubmitAttempted.value && !isNameValid.value ? [REQUIRED_MESSAGE] : [],
)
const categoryErrorMessages = computed<string[]>(() =>
  hasSubmitAttempted.value && !isCategoryValid.value ? [REQUIRED_MESSAGE] : [],
)
const intervalErrorMessages = computed<string[]>(() =>
  hasSubmitAttempted.value && !isIntervalValid.value ? [INTERVAL_RANGE_MESSAGE] : [],
)

const submitForm = async (): Promise<void> => {
  hasSubmitAttempted.value = true
  if (!isFormValid.value || category.value === null) {
    return
  }

  const input: AssetTypeInput = {
    name: name.value.trim(),
    category: category.value,
    inspection_interval_days: Number(intervalText.value),
  }
  isSaving.value = true
  errorMessage.value = null
  try {
    const savedAssetType = props.assetType === null
      ? await createAssetType(input)
      : await updateAssetType(props.assetType.id, input)
    emit('saved', savedAssetType)
  } catch (error: unknown) {
    errorMessage.value = getErrorDetail(error) ?? handleNetworkError(error)
  } finally {
    isSaving.value = false
  }
}
</script>
