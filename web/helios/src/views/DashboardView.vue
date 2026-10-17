<template>
  <v-container>
    <h1 class="flex items-center justify-center gap-2 text-center text-2xl font-semibold">
      Dashboard
      <EasyToolTip text="Live status of the FieldOps services." />
    </h1>
    <v-progress-circular
      v-if="isLoading"
      class="mx-auto block"
      indeterminate
      data-testid="atlas-health-loading"
    />
    <p
      v-else-if="atlasHealthStatus !== null"
      data-testid="atlas-health-status"
    >
      Atlas service: {{ atlasHealthStatus }}
    </p>
    <v-alert
      v-if="errorMessage !== null"
      type="error"
      :text="errorMessage"
      data-testid="atlas-health-error"
    />
  </v-container>
</template>

<script setup lang="ts">
import { fetchAtlasHealth } from '@/api/health'
import { handleNetworkError } from '@/api/errors'
import EasyToolTip from '@/components/EasyToolTip.vue'
import { onMounted, ref } from 'vue'

const isLoading = ref<boolean>(true)
const atlasHealthStatus = ref<string | null>(null)
const errorMessage = ref<string | null>(null)

const loadAtlasHealth = async (): Promise<void> => {
  isLoading.value = true
  errorMessage.value = null
  try {
    const healthStatus = await fetchAtlasHealth()
    atlasHealthStatus.value = healthStatus.status
  } catch (error: unknown) {
    errorMessage.value = handleNetworkError(error)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadAtlasHealth()
})
</script>
