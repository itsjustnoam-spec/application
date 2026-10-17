import { ref } from 'vue'

import { handleNetworkError } from '@/api/errors'
import type { ListParams, Page } from '@/models/page'

const PAGE_SIZE = 20
const SEARCH_DEBOUNCE_MS = 300
const FIRST_PAGE = 1

const usePagedList = <Item>(fetchPage: (params: ListParams) => Promise<Page<Item>>) => {
  const items = ref<Item[]>([])
  const total = ref<number>(0)
  const page = ref<number>(FIRST_PAGE)
  const searchText = ref<string>('')
  const isLoading = ref<boolean>(false)
  const errorMessage = ref<string | null>(null)
  let searchTimer: ReturnType<typeof setTimeout> | null = null

  const loadPage = async (): Promise<void> => {
    isLoading.value = true
    errorMessage.value = null
    try {
      const result = await fetchPage({
        limit: PAGE_SIZE,
        offset: (page.value - FIRST_PAGE) * PAGE_SIZE,
        query: searchText.value,
      })
      items.value = result.items
      total.value = result.total
    } catch (error: unknown) {
      errorMessage.value = handleNetworkError(error)
    } finally {
      isLoading.value = false
    }
  }

  const setPage = (nextPage: number): void => {
    page.value = nextPage
    void loadPage()
  }

  const setSearchText = (text: string): void => {
    searchText.value = text
    if (searchTimer !== null) {
      clearTimeout(searchTimer)
    }
    searchTimer = setTimeout(() => {
      page.value = FIRST_PAGE
      void loadPage()
    }, SEARCH_DEBOUNCE_MS)
  }

  return {
    items,
    total,
    page,
    searchText,
    isLoading,
    errorMessage,
    loadPage,
    setPage,
    setSearchText,
  }
}

export { PAGE_SIZE, SEARCH_DEBOUNCE_MS, usePagedList }
