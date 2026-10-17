import { flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { VAutocomplete } from 'vuetify/components'

import ActiveEntitySelect from '@/components/ActiveEntitySelect.vue'
import { SEARCH_DEBOUNCE_MS } from '@/utils/use-paged-list'

import { mountWithPlugins } from '../../utils/mount'

const NORTH_DEPOT_OPTION = { value: 1, title: 'North Depot' }
const SOUTH_DEPOT_OPTION = { value: 2, title: 'South Depot' }

const mountActiveEntitySelect = (
  fetchOptions: (query: string) => Promise<typeof NORTH_DEPOT_OPTION[]>,
  modelValue: number | null = null,
  selectedOption: typeof NORTH_DEPOT_OPTION | null = null,
) => {
  return mountWithPlugins(ActiveEntitySelect, {
    props: {
      modelValue,
      label: 'Site',
      testId: 'asset-site-select',
      selectedOption,
      errorMessages: [],
      fetchOptions,
    },
  })
}

afterEach(() => {
  vi.useRealTimers()
})

describe('ActiveEntitySelect', () => {
  it('requests options for the typed search text once the typing pauses', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    const fetchOptions = vi.fn().mockResolvedValue([NORTH_DEPOT_OPTION])
    const wrapper = mountActiveEntitySelect(fetchOptions)
    await flushPromises()

    const searchInput = wrapper.getComponent(VAutocomplete).get('input')
    await searchInput.setValue('N')
    await searchInput.setValue('No')
    await searchInput.setValue('North')
    vi.advanceTimersByTime(SEARCH_DEBOUNCE_MS)
    await flushPromises()

    expect(fetchOptions).toHaveBeenCalledTimes(2)
    expect(fetchOptions).toHaveBeenLastCalledWith('North')
  })

  it('keeps the selected option listed when it is not in the fetched results', async () => {
    const fetchOptions = vi.fn().mockResolvedValue([SOUTH_DEPOT_OPTION])
    const wrapper = mountActiveEntitySelect(fetchOptions, 1, NORTH_DEPOT_OPTION)
    await flushPromises()

    expect(wrapper.text()).toContain('North Depot')
  })
})
