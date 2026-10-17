<template>
  <v-card>
    <v-card-title class="flex items-center justify-center gap-2 text-center">
      {{ dialogTitle }}
      <EasyToolTip text="A site is a physical location where assets are installed. Its timezone is used for scheduling inspections." />
    </v-card-title>
    <v-card-text>
      <v-text-field
        v-model="nameInput"
        label="Name"
        :error-messages="nameErrorMessages"
        data-testid="site-name-input"
      />
      <v-text-field
        v-model="addressInput"
        label="Address"
        :error-messages="addressErrorMessages"
        data-testid="site-address-input"
      />
      <v-autocomplete
        v-model="timezoneInput"
        :items="TIMEZONE_OPTIONS"
        label="Timezone"
        :error-messages="timezoneErrorMessages"
        data-testid="site-timezone-input"
      />
      <v-alert
        v-if="formErrorMessage !== null"
        type="error"
        :text="formErrorMessage"
        data-testid="site-form-error"
      />
    </v-card-text>
    <v-card-actions class="justify-end">
      <v-btn
        variant="text"
        data-testid="site-form-cancel-button"
        @click="emit('cancel')"
      >
        Cancel
      </v-btn>
      <v-btn
        color="primary"
        :loading="isSubmitting"
        data-testid="site-form-submit-button"
        @click="submitSite"
      >
        Save
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { createSite, updateSite } from '@/api/sites'
import EasyToolTip from '@/components/EasyToolTip.vue'
import type { Site, SiteInput } from '@/models/site'
import { getRequiredTextError, getSelectionError } from '@/utils/formRules'
import { classifyWriteError, INVALID_VALUES_MESSAGE } from '@/utils/writeErrors'
import { computed, ref, watch } from 'vue'

const NAME_MAX_LENGTH = 100
const ADDRESS_MAX_LENGTH = 255
const DUPLICATE_NAME_MESSAGE = 'A site with this name already exists.'
const TIMEZONE_OPTIONS: string[] = Intl.supportedValuesOf('timeZone')

const props = defineProps<{
  site: Site | null
}>()

const emit = defineEmits<{
  saved: []
  cancel: []
  'already-deleted': []
}>()

const nameInput = ref<string>(props.site === null ? '' : props.site.name)
const addressInput = ref<string>(props.site === null ? '' : props.site.address)
const timezoneInput = ref<string | null>(props.site === null ? null : props.site.timezone)
const hasAttemptedSubmit = ref<boolean>(false)
const isNameTaken = ref<boolean>(false)
const isSubmitting = ref<boolean>(false)
const formErrorMessage = ref<string | null>(null)

const dialogTitle = computed<string>(() => (props.site === null ? 'New site' : 'Edit site'))

const nameValidationError = computed<string | null>(() =>
  getRequiredTextError(nameInput.value, NAME_MAX_LENGTH),
)
const addressValidationError = computed<string | null>(() =>
  getRequiredTextError(addressInput.value, ADDRESS_MAX_LENGTH),
)
const timezoneValidationError = computed<string | null>(() =>
  getSelectionError(timezoneInput.value),
)

const hasValidationErrors = computed<boolean>(
  () =>
    nameValidationError.value !== null ||
    addressValidationError.value !== null ||
    timezoneValidationError.value !== null,
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

const addressErrorMessages = computed<string[]>(() => {
  const addressError = addressValidationError.value
  if (!hasAttemptedSubmit.value || addressError === null) {
    return []
  }
  return [addressError]
})

const timezoneErrorMessages = computed<string[]>(() => {
  const timezoneError = timezoneValidationError.value
  if (!hasAttemptedSubmit.value || timezoneError === null) {
    return []
  }
  return [timezoneError]
})

const buildSiteInput = (): SiteInput => {
  return {
    name: nameInput.value.trim(),
    address: addressInput.value.trim(),
    timezone: timezoneInput.value ?? '',
  }
}

const submitSite = async (): Promise<void> => {
  hasAttemptedSubmit.value = true
  if (hasValidationErrors.value) {
    return
  }
  isSubmitting.value = true
  formErrorMessage.value = null
  try {
    if (props.site === null) {
      await createSite(buildSiteInput())
    } else {
      await updateSite(props.site.id, buildSiteInput())
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
