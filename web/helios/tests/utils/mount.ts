import { mount, type ComponentMountingOptions } from '@vue/test-utils'
import type { Component } from 'vue'

import { createAppVuetify } from '@/plugins/vuetify'

const mountWithPlugins = <Props>(
  component: Component,
  options: ComponentMountingOptions<Props> = {},
) => {
  const globalOptions = options.global
  const extraPlugins =
    globalOptions !== undefined && globalOptions.plugins !== undefined ? globalOptions.plugins : []
  return mount(component, {
    ...options,
    global: {
      ...options.global,
      plugins: [createAppVuetify(), ...extraPlugins],
    },
  })
}

export { mountWithPlugins }
