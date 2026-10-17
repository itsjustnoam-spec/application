import { ref } from 'vue'

import { handleNetworkError } from '@/api/errors'
import type { ListFilterValue, ListParams, Page } from '@/models/page'

const PAGE_SIZE = 20
const SEARCH_DEBOUNCE_MS = 300
const FIRST_PAGE = 1

const usePagedList = <Item>(fetchPage: (params: ListParams) => Promise<Page<Item>>) => {
  const items = ref<Item[]>([])
  const total = ref<number>(0)
  const page = ref<number>(FIRST_PAGE)
  const searchText = ref<string>('')
  const filters = ref<Record<string, ListFilterValue>>({})
  const sortKey = ref<string | null>(null)
  const sortDirection = ref<'asc' | 'desc'>('asc')
  const isLoading = ref<boolean>(false)
  const errorMessage = ref<string | null>(null)
  let searchTimer: ReturnType<typeof setTimeout> | null = null
  let latestRequestId = 0

  const loadPage = async (): Promise<void> => {
    latestRequestId += 1
    const requestId = latestRequestId
    isLoading.value = true
    errorMessage.value = null
    try {
      const result = await fetchPage({
        limit: PAGE_SIZE,
        offset: (page.value - FIRST_PAGE) * PAGE_SIZE,
        query: searchText.value,
        filters: filters.value,
        sort: sortKey.value ?? undefined,
        direction: sortKey.value === null ? undefined : sortDirection.value,
      })
      if (requestId === latestRequestId) {
        const isPastLastPage = result.items.length === 0 && page.value > FIRST_PAGE
        if (isPastLastPage) {
          page.value = Math.max(FIRST_PAGE, Math.ceil(result.total / PAGE_SIZE))
          await loadPage()
          return
        }
        items.value = result.items
        total.value = result.total
      }
    } catch (error: unknown) {
      if (requestId === latestRequestId) {
        errorMessage.value = handleNetworkError(error)
      }
    } finally {
      if (requestId === latestRequestId) {
        isLoading.value = false
      }
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

  const setFilters = (nextFilters: Record<string, ListFilterValue>): void => {
    filters.value = nextFilters
    page.value = FIRST_PAGE
    void loadPage()
  }

  const setSort = (key: string | null, direction: 'asc' | 'desc'): void => {
    sortKey.value = key
    sortDirection.value = direction
    page.value = FIRST_PAGE
    void loadPage()
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
    setFilters,
    setSort,
  }
}

export { PAGE_SIZE, SEARCH_DEBOUNCE_MS, usePagedList }
