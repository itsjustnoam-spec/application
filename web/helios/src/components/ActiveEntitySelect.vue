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

interface ActiveEntitySelectProps {
  modelValue: number | null
  label: string
  testId: string
  selectedOption: SelectOption | null
  errorMessages: string[]
  fetchOptions: (query: string) => Promise<SelectOption[]>
}

interface ActiveEntitySelectEmits {
  'update:modelValue': [number | null]
}


export type { ActiveEntitySelectEmits, ActiveEntitySelectProps }
</script>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { handleNetworkError } from '@/api/errors'
import { SEARCH_DEBOUNCE_MS } from '@/utils/use-paged-list'

const emit = defineEmits<ActiveEntitySelectEmits>()

const props = defineProps<ActiveEntitySelectProps>()

const fetchedOptions = ref<SelectOption[]>([])
const chosenOption = ref<SelectOption | null>(props.selectedOption)
const isLoading = ref<boolean>(false)
const loadErrorMessage = ref<string | null>(null)
let searchTimer: ReturnType<typeof setTimeout> | null = null
let latestRequestId = 0

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
  latestRequestId += 1
  const requestId = latestRequestId
  isLoading.value = true
  loadErrorMessage.value = null
  try {
    const result = await props.fetchOptions(query)
    if (requestId === latestRequestId) {
      fetchedOptions.value = result
    }
  } catch (error: unknown) {
    if (requestId === latestRequestId) {
      loadErrorMessage.value = handleNetworkError(error)
    }
  } finally {
    if (requestId === latestRequestId) {
      isLoading.value = false
    }
  }
}

const onSearch = (query: string): void => {
  if (searchTimer !== null) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    void loadOptions(query)
  }, SEARCH_DEBOUNCE_MS)
}

const onSelect = (value: number | null): void => {
  chosenOption.value = options.value.find((option) => option.value === value) ?? null
  emit('update:modelValue', value)
}

onMounted(() => {
  void loadOptions('')
})

onUnmounted(() => {
  if (searchTimer !== null) {
    clearTimeout(searchTimer)
  }
})
</script>
