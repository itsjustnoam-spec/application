<template>
  <v-card>
    <v-card-title class="flex items-center justify-center gap-2 text-center">
      {{ dialogTitle }}
      <EasyToolTip text="An asset type groups assets of the same kind and sets how often they are inspected." />
    </v-card-title>
    <v-card-text>
      <v-text-field
        v-model="nameInput"
        label="Name"
        :error-messages="nameErrorMessages"
        data-testid="asset-type-name-input"
      />
      <v-text-field
        v-model="categoryInput"
        label="Category"
        :error-messages="categoryErrorMessages"
        data-testid="asset-type-category-input"
      />
      <v-text-field
        v-model="intervalInput"
        label="Inspection interval (days)"
        type="number"
        :error-messages="intervalErrorMessages"
        data-testid="asset-type-interval-input"
      >
        <template #append-inner>
          <EasyToolTip text="Days between inspections of an asset of this type." />
        </template>
      </v-text-field>
      <v-alert
        v-if="formErrorMessage !== null"
        type="error"
        :text="formErrorMessage"
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
        :loading="isSubmitting"
        data-testid="asset-type-form-submit-button"
        @click="submitAssetType"
      >
        Save
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { createAssetType, updateAssetType } from '@/api/assetTypes'
import EasyToolTip from '@/components/EasyToolTip.vue'
import type { AssetType, AssetTypeInput } from '@/models/assetType'
import { getRequiredTextError, getWholeNumberRangeError } from '@/utils/formRules'
import { classifyWriteError, INVALID_VALUES_MESSAGE } from '@/utils/writeErrors'
import { computed, ref, watch } from 'vue'

const NAME_MAX_LENGTH = 100
const CATEGORY_MAX_LENGTH = 100
const MIN_INSPECTION_INTERVAL_DAYS = 1
const MAX_INSPECTION_INTERVAL_DAYS = 3650
const DUPLICATE_NAME_MESSAGE = 'An asset type with this name already exists.'

const props = defineProps<{
  assetType: AssetType | null
}>()

const emit = defineEmits<{
  saved: []
  cancel: []
  'already-deleted': []
}>()

const nameInput = ref<string>(props.assetType === null ? '' : props.assetType.name)
const categoryInput = ref<string>(props.assetType === null ? '' : props.assetType.category)
const intervalInput = ref<string>(
  props.assetType === null ? '' : String(props.assetType.inspection_interval_days),
)
const hasAttemptedSubmit = ref<boolean>(false)
const isNameTaken = ref<boolean>(false)
const isSubmitting = ref<boolean>(false)
const formErrorMessage = ref<string | null>(null)

const dialogTitle = computed<string>(() => (props.assetType === null ? 'New asset type' : 'Edit asset type'))

const nameValidationError = computed<string | null>(() =>
  getRequiredTextError(nameInput.value, NAME_MAX_LENGTH),
)
const categoryValidationError = computed<string | null>(() =>
  getRequiredTextError(categoryInput.value, CATEGORY_MAX_LENGTH),
)
const intervalValidationError = computed<string | null>(() =>
  getWholeNumberRangeError(
    intervalInput.value,
    MIN_INSPECTION_INTERVAL_DAYS,
    MAX_INSPECTION_INTERVAL_DAYS,
  ),
)

const hasValidationErrors = computed<boolean>(
  () =>
    nameValidationError.value !== null ||
    categoryValidationError.value !== null ||
    intervalValidationError.value !== null,
)

const nameErrorMessages = computed<string[]>(() => {
  if (isNameTaken.value) {
    return [DUPLICATE_NAME_MESSAGE]
  }
  const nameError = nameValidationError.value
  if (!hasAttemptedSubmit.value || nameError === null) {
    return []
  }
  return [nameError]
})

const categoryErrorMessages = computed<string[]>(() => {
  const categoryError = categoryValidationError.value
  if (!hasAttemptedSubmit.value || categoryError === null) {
    return []
  }
  return [categoryError]
})

const intervalErrorMessages = computed<string[]>(() => {
  const intervalError = intervalValidationError.value
  if (!hasAttemptedSubmit.value || intervalError === null) {
    return []
  }
  return [intervalError]
})

const buildAssetTypeInput = (): AssetTypeInput => {
  return {
    name: nameInput.value.trim(),
    category: categoryInput.value.trim(),
    inspection_interval_days: Number(intervalInput.value.trim()),
  }
}

const submitAssetType = async (): Promise<void> => {
  hasAttemptedSubmit.value = true
  if (hasValidationErrors.value) {
    return
  }
  isSubmitting.value = true
  formErrorMessage.value = null
  try {
    if (props.assetType === null) {
      await createAssetType(buildAssetTypeInput())
    } else {
      await updateAssetType(props.assetType.id, buildAssetTypeInput())
    }
    emit('saved')
  } catch (error: unknown) {
    const failure = classifyWriteError(error)
    if (failure.kind === 'name-taken') {
      isNameTaken.value = true
    } else if (failure.kind === 'already-deleted') {
      emit('already-deleted')
    } else if (failure.kind === 'invalid-values') {
      formErrorMessage.value = INVALID_VALUES_MESSAGE
    } else {
      formErrorMessage.value = failure.message
    }
  } finally {
    isSubmitting.value = false
  }
}

watch(nameInput, () => {
  isNameTaken.value = false
})
</script>
