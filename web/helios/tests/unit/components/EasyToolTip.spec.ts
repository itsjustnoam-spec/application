import { flushPromises } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import EasyToolTip from '@/components/EasyToolTip.vue'

import { mountWithPlugins } from '../../utils/mount'

describe('EasyToolTip', () => {
  it('shows the tooltip text when the icon is hovered', async () => {
    const wrapper = mountWithPlugins(EasyToolTip, {
      props: { text: 'Live status of the FieldOps services.' },
    })

    await wrapper.get('[data-testid="easy-tooltip-icon"]').trigger('mouseenter')
    await flushPromises()

    expect(document.body.textContent).toContain('Live status of the FieldOps services.')
    wrapper.unmount()
  })
})
