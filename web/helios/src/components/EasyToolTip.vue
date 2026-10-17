<template>
  <v-tooltip :text="text" location="top">
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
export const DEFAULT_TOOLTIP_ICON = 'mdi-information'

export interface EasyToolTipProps {
  text: string
  icon?: string
}
</script>

<script setup lang="ts">
withDefaults(defineProps<EasyToolTipProps>(), {
  icon: DEFAULT_TOOLTIP_ICON,
})
</script>
