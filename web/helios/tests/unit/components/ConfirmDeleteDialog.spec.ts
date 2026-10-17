import { describe, expect, it } from 'vitest'

import ConfirmDeleteDialog from '@/components/ConfirmDeleteDialog.vue'
import { mountWithPlugins } from '../../utils/mount'

const CANCEL_ERROR_MESSAGE = 'Cannot archive this site right now.'

const mountConfirmDeleteDialog = (errorMessage: string | null = null) => {
  return mountWithPlugins(ConfirmDeleteDialog, {
    props: {
      title: 'Archive site',
      message: 'Archive "North Depot"? It will be hidden from lists.',
      isLoading: false,
      errorMessage,
    },
  })
}

describe('ConfirmDeleteDialog', () => {
  it('emits confirm when the archive button is clicked', async () => {
    const wrapper = mountConfirmDeleteDialog()

    await wrapper.get('[data-testid="confirm-delete-button"]').trigger('click')

    expect(wrapper.emitted('confirm')).toHaveLength(1)
  })

  it('emits cancel and not confirm when cancel is clicked', async () => {
    const wrapper = mountConfirmDeleteDialog()

    await wrapper.get('[data-testid="cancel-delete-button"]').trigger('click')

    expect(wrapper.emitted('cancel')).toHaveLength(1)
    expect(wrapper.emitted('confirm')).toBeUndefined()
  })

  it('shows the error message when one is provided', () => {
    const wrapper = mountConfirmDeleteDialog(CANCEL_ERROR_MESSAGE)

    expect(wrapper.get('[data-testid="confirm-delete-error"]').text()).toContain(
      CANCEL_ERROR_MESSAGE,
    )
  })
})
