<template>
  <v-card>
    <v-card-title class="text-center" data-testid="delete-confirm-title">
      {{ title }}
    </v-card-title>
    <v-card-text data-testid="delete-confirm-message">{{ message }}</v-card-text>
    <v-card-actions class="justify-end">
      <v-btn
        variant="text"
        data-testid="delete-cancel-button"
        @click="emit('cancel')"
      >
        Cancel
      </v-btn>
      <v-btn
        color="error"
        :loading="isLoading"
        data-testid="delete-confirm-button"
        @click="emit('confirm')"
      >
        Delete
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

defineProps<{
  title: string
  message: string
  isLoading: boolean
}>()
</script>
