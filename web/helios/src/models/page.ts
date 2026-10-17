interface Page<Item> {
  items: Item[]
  total: number
  limit: number
  offset: number
}

interface ListParams {
  limit: number
  offset: number
  query: string | null
}

export type { ListParams, Page }
