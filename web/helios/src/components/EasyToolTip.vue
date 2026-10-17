<template>
  <v-tooltip
    :text="text"
    location="top"
  >
    <template #activator="{ props: activatorProps }">
      <v-icon
        v-bind="activatorProps"
        :icon="icon"
        size="small"
        data-testid="easy-tooltip-icon"
      />
    </template>
  </v-tooltip>
</template>

<script lang="ts">
const DEFAULT_TOOLTIP_ICON = 'mdi-information'

interface Props {
  text: string
  icon?: string
}
</script>

<script setup lang="ts">
withDefaults(defineProps<Props>(), {
  icon: DEFAULT_TOOLTIP_ICON,
})
</script>
