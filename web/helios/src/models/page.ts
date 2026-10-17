interface Page<Item> {
  items: Item[]
  total: number
  limit: number
  offset: number
}

type ListFilterValue = string | number | null

interface ListParams {
  limit: number
  offset: number
  query: string | null
  filters?: Record<string, ListFilterValue>
  sort?: string
  direction?: 'asc' | 'desc'
}

export type { ListFilterValue, ListParams, Page }
