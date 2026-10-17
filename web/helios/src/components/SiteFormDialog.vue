<template>
  <v-card>
    <v-card-title class="flex items-center justify-center gap-2 text-center">
      {{ dialogTitle }}
      <EasyToolTip text="Sites group assets by location. Their timezone drives inspection schedules." />
    </v-card-title>
    <v-card-text>
      <v-text-field
        v-model="name"
        label="Name"
        :error-messages="nameErrorMessages"
        :counter="NAME_MAX_LENGTH"
        data-testid="site-name-input"
      />
      <v-text-field
        v-model="address"
        label="Address"
        :error-messages="addressErrorMessages"
        :counter="ADDRESS_MAX_LENGTH"
        data-testid="site-address-input"
      />
      <div class="flex items-center gap-2">
        <EasyToolTip text="IANA timezone name, for example Europe/Berlin." />
      </div>
      <v-autocomplete
        v-model="timezone"
        label="Timezone"
        :items="TIMEZONE_OPTIONS"
        :error-messages="timezoneErrorMessages"
        data-testid="site-timezone-input"
      />
      <v-alert
        v-if="errorMessage !== null"
        type="error"
        :text="errorMessage"
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
        :loading="isSaving"
        :disabled="isSaving"
        data-testid="site-form-save-button"
        @click="submitForm"
      >
        Save
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import type { Site } from '@/models/site'
import { TIMEZONE_OPTIONS } from '@/utils/timezones'

interface Props {
  site: Site | null
}

interface Emits {
  'saved': [Site]
  'cancel': []
}

const NAME_MAX_LENGTH = 100
const ADDRESS_MAX_LENGTH = 500
const REQUIRED_MESSAGE = 'This field is required.'
const TOO_LONG_MESSAGE_PREFIX = 'Too long: max'
</script>

<script setup lang="ts">
import { computed, onBeforeMount, ref } from 'vue'

import { createSite, updateSite } from '@/api/sites'
import { describeRequestError } from '@/api/errors'
import EasyToolTip from '@/components/EasyToolTip.vue'
import type { SiteInput } from '@/models/site'

const emit = defineEmits<Emits>()

const props = defineProps<Props>()

const name = ref<string>('')
const address = ref<string>('')
const timezone = ref<string | null>(null)
const hasSubmitAttempted = ref<boolean>(false)
const isSaving = ref<boolean>(false)
const errorMessage = ref<string | null>(null)

const dialogTitle = computed<string>(() => (props.site === null ? 'New site' : 'Edit site'))

const isNameValid = computed<boolean>(
  () => name.value.trim().length > 0 && name.value.length <= NAME_MAX_LENGTH,
)
const isAddressValid = computed<boolean>(
  () => address.value.trim().length > 0 && address.value.length <= ADDRESS_MAX_LENGTH,
)
const isTimezoneValid = computed<boolean>(() => timezone.value !== null)
const isFormValid = computed<boolean>(
  () => isNameValid.value && isAddressValid.value && isTimezoneValid.value,
)

const nameErrorMessages = computed<string[]>(() => {
  if (!hasSubmitAttempted.value || isNameValid.value) {
    return []
  }
  return name.value.length > NAME_MAX_LENGTH
    ? [`${TOO_LONG_MESSAGE_PREFIX} ${NAME_MAX_LENGTH} characters.`]
    : [REQUIRED_MESSAGE]
})

const addressErrorMessages = computed<string[]>(() => {
  if (!hasSubmitAttempted.value || isAddressValid.value) {
    return []
  }
  return address.value.length > ADDRESS_MAX_LENGTH
    ? [`${TOO_LONG_MESSAGE_PREFIX} ${ADDRESS_MAX_LENGTH} characters.`]
    : [REQUIRED_MESSAGE]
})

const timezoneErrorMessages = computed<string[]>(() =>
  hasSubmitAttempted.value && !isTimezoneValid.value ? [REQUIRED_MESSAGE] : [],
)

const submitForm = async (): Promise<void> => {
  hasSubmitAttempted.value = true
  if (!isFormValid.value || timezone.value === null) {
    return
  }

  const input: SiteInput = {
    name: name.value.trim(),
    address: address.value.trim(),
    timezone: timezone.value,
  }
  isSaving.value = true
  errorMessage.value = null
  try {
    if (props.site === null) {
      emit('saved', await createSite(input))
    } else {
      emit('saved', await updateSite(props.site.id, input))
    }
  } catch (error: unknown) {
    errorMessage.value = describeRequestError(error)
  } finally {
    isSaving.value = false
  }
}

function fillFormFromSite() {
  if (props.site === null) {
    return
  }
  name.value = props.site.name
  address.value = props.site.address
  timezone.value = props.site.timezone
}

onBeforeMount(() => {
  fillFormFromSite()
})
</script>
