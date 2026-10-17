import { createRouter, createWebHistory, type RouteRecordRaw, type RouterHistory } from 'vue-router'

import AdminView from '@/views/AdminView.vue'
import AssetTypesView from '@/views/AssetTypesView.vue'
import AssetsView from '@/views/AssetsView.vue'
import DashboardView from '@/views/DashboardView.vue'
import InspectionsView from '@/views/InspectionsView.vue'
import SitesView from '@/views/SitesView.vue'
import WorkOrdersView from '@/views/WorkOrdersView.vue'

const APP_ROUTES: RouteRecordRaw[] = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'dashboard', component: DashboardView },
  { path: '/assets', name: 'assets', component: AssetsView },
  { path: '/work-orders', name: 'work-orders', component: WorkOrdersView },
  { path: '/inspections', name: 'inspections', component: InspectionsView },
  {
    path: '/admin',
    name: 'admin',
    component: AdminView,
    redirect: '/admin/sites',
    children: [
      { path: 'sites', name: 'admin-sites', component: SitesView },
      { path: 'asset-types', name: 'admin-asset-types', component: AssetTypesView },
    ],
  },
]

const createAppRouter = (history: RouterHistory = createWebHistory()) => {
  return createRouter({
    history,
    routes: APP_ROUTES,
  })
}

export { APP_ROUTES, createAppRouter }
