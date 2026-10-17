import { flushPromises } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import { updateSite } from '@/api/sites'
import SiteFormDialog from '@/components/SiteFormDialog.vue'
import { makeSite } from '../../mocks/factories/site'
import { mountWithPlugins } from '../../utils/mount'

vi.mock('@/api/sites')

const REQUIRED_MESSAGE = 'This field is required.'
const SITE_NAME_TAKEN_DETAIL = 'A site with this name already exists'

describe('SiteFormDialog', () => {
  it('shows the required message when submitted with an empty name', async () => {
    const wrapper = mountWithPlugins(SiteFormDialog, {
      props: { site: null },
      global: { stubs: { teleport: true } },
    })

    await wrapper.get('[data-testid="site-name-input"] input').setValue('')
    await wrapper.get('[data-testid="site-form-save-button"]').trigger('click')

    expect(wrapper.text()).toContain(REQUIRED_MESSAGE)
  })

  it('emits saved with the updated site after a valid submit', async () => {
    const savedSite = makeSite({ id: 3, name: 'Renamed Depot' })
    vi.mocked(updateSite).mockResolvedValue(savedSite)
    const wrapper = mountWithPlugins(SiteFormDialog, {
      props: { site: makeSite({ id: 3 }) },
      global: { stubs: { teleport: true } },
    })

    await wrapper.get('[data-testid="site-name-input"] input').setValue('Renamed Depot')
    await wrapper.get('[data-testid="site-form-save-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.emitted('saved')).toEqual([[savedSite]])
  })

  it('shows the backend detail when the server rejects a duplicate name', async () => {
    vi.mocked(updateSite).mockRejectedValue(new ApiError(409, SITE_NAME_TAKEN_DETAIL))
    const wrapper = mountWithPlugins(SiteFormDialog, {
      props: { site: makeSite({ id: 3 }) },
      global: { stubs: { teleport: true } },
    })

    await wrapper.get('[data-testid="site-form-save-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('[data-testid="site-form-error"]').text()).toContain(SITE_NAME_TAKEN_DETAIL)
  })

  it('emits cancel when the cancel button is clicked', async () => {
    const wrapper = mountWithPlugins(SiteFormDialog, {
      props: { site: null },
      global: { stubs: { teleport: true } },
    })

    await wrapper.get('[data-testid="site-form-cancel-button"]').trigger('click')

    expect(wrapper.emitted('cancel')).toHaveLength(1)
  })

  it('pre-fills the fields when editing an existing site', () => {
    const wrapper = mountWithPlugins(SiteFormDialog, {
      props: { site: makeSite({ name: 'South Depot', address: '9 Dock Road' }) },
      global: { stubs: { teleport: true } },
    })

    expect(wrapper.get('[data-testid="site-name-input"] input').element).toHaveProperty(
      'value',
      'South Depot',
    )
    expect(wrapper.get('[data-testid="site-address-input"] input').element).toHaveProperty(
      'value',
      '9 Dock Road',
    )
  })
})
