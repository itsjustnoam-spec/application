<template>
  <v-autocomplete
    :model-value="modelValue"
    :items="options"
    :label="label"
    :loading="isLoading"
    :error-messages="errorMessages"
    :data-testid="testId"
    no-filter
    clearable
    @update:search="onSearch"
    @update:model-value="onSelect"
  />
</template>

<script lang="ts">
import type { SelectOption } from '@/models/select-option'

interface Props {
  modelValue: number | null
  label: string
  testId: string
  selectedOption: SelectOption | null
  errorMessages: string[]
  fetchOptions: (query: string) => Promise<SelectOption[]>
}

interface Emits {
  'update:modelValue': [number | null]
}
</script>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { handleNetworkError } from '@/api/errors'
import { SEARCH_DEBOUNCE_MS } from '@/utils/use-paged-list'

const emit = defineEmits<Emits>()

const props = defineProps<Props>()

const fetchedOptions = ref<SelectOption[]>([])
const chosenOption = ref<SelectOption | null>(props.selectedOption)
const isLoading = ref<boolean>(false)
const loadErrorMessage = ref<string | null>(null)
const searchTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const latestRequestId = ref<number>(0)

const options = computed<SelectOption[]>(() => {
  const chosen = chosenOption.value
  if (chosen === null || fetchedOptions.value.some((option) => option.value === chosen.value)) {
    return fetchedOptions.value
  }

  return [chosen, ...fetchedOptions.value]
})

const errorMessages = computed<string[]>(() =>
  loadErrorMessage.value === null
    ? props.errorMessages
    : [...props.errorMessages, loadErrorMessage.value],
)

const loadOptions = async (query: string): Promise<void> => {
  latestRequestId.value += 1
  const requestId = latestRequestId.value
  isLoading.value = true
  loadErrorMessage.value = null
  try {
    const result = await props.fetchOptions(query)
    if (requestId === latestRequestId.value) {
      fetchedOptions.value = result
    }
  } catch (error: unknown) {
    if (requestId === latestRequestId.value) {
      loadErrorMessage.value = handleNetworkError(error)
    }
  } finally {
    if (requestId === latestRequestId.value) {
      isLoading.value = false
    }
  }
}

const onSearch = (query: string): void => {
  if (searchTimer.value !== null) {
    clearTimeout(searchTimer.value)
  }
  searchTimer.value = setTimeout(() => {
    loadOptions(query)
  }, SEARCH_DEBOUNCE_MS)
}

const onSelect = (value: number | null): void => {
  const matchingOption = options.value.find((option) => option.value === value)
  if (matchingOption === undefined) {
    chosenOption.value = null
  } else {
    chosenOption.value = matchingOption
  }
  emit('update:modelValue', value)
}

onMounted(() => {
  loadOptions('')
})

onUnmounted(() => {
  if (searchTimer.value !== null) {
    clearTimeout(searchTimer.value)
  }
})
</script>
