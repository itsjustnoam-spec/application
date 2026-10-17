<template>
  <v-card>
    <v-card-title class="text-center" data-testid="confirm-delete-title">
      {{ title }}
    </v-card-title>
    <v-card-text>
      <p>{{ message }}</p>
      <v-alert
        v-if="errorMessage !== null"
        class="mt-4"
        type="error"
        :text="errorMessage"
        data-testid="confirm-delete-error"
      />
    </v-card-text>
    <v-card-actions class="justify-end">
      <v-btn
        variant="text"
        :disabled="isLoading"
        data-testid="cancel-delete-button"
        @click="emit('cancel')"
      >
        Cancel
      </v-btn>
      <v-btn
        color="error"
        :loading="isLoading"
        data-testid="confirm-delete-button"
        @click="emit('confirm')"
      >
        Archive
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
interface ConfirmDeleteProps {
  title: string
  message: string
  isLoading: boolean
  errorMessage: string | null
}

interface ConfirmDeleteEmits {
  'confirm': []
  'cancel': []
}

export type { ConfirmDeleteEmits, ConfirmDeleteProps }
</script>

<script setup lang="ts">
const emit = defineEmits<ConfirmDeleteEmits>()

defineProps<ConfirmDeleteProps>()
</script>
