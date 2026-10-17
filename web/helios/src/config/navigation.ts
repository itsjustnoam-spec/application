export interface NavigationItem {
  title: string
  path: string
  icon: string
}

export const NAVIGATION_ITEMS: NavigationItem[] = [
  { title: 'Dashboard', path: '/dashboard', icon: 'mdi-view-dashboard' },
  { title: 'Assets', path: '/assets', icon: 'mdi-factory' },
  { title: 'Work Orders', path: '/work-orders', icon: 'mdi-clipboard-list' },
  { title: 'Inspections', path: '/inspections', icon: 'mdi-magnify' },
  { title: 'Sites', path: '/sites', icon: 'mdi-map-marker' },
  { title: 'Asset Types', path: '/asset-types', icon: 'mdi-tag-multiple' },
  { title: 'Admin', path: '/admin', icon: 'mdi-cog' },
]
