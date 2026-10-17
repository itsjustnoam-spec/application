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

interface EasyToolTipProps {
  text: string
  icon?: string
}

export type { EasyToolTipProps }
export { DEFAULT_TOOLTIP_ICON }
</script>

<script setup lang="ts">
withDefaults(defineProps<EasyToolTipProps>(), {
  icon: DEFAULT_TOOLTIP_ICON,
})
</script>
