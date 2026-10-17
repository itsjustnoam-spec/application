import { createRouter, createWebHistory, type RouteRecordRaw, type RouterHistory } from 'vue-router'

import AdminView from '@/views/AdminView.vue'
import AssetsView from '@/views/AssetsView.vue'
import DashboardView from '@/views/DashboardView.vue'
import InspectionsView from '@/views/InspectionsView.vue'
import WorkOrdersView from '@/views/WorkOrdersView.vue'

export const APP_ROUTES: RouteRecordRaw[] = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'dashboard', component: DashboardView },
  { path: '/assets', name: 'assets', component: AssetsView },
  { path: '/work-orders', name: 'work-orders', component: WorkOrdersView },
  { path: '/inspections', name: 'inspections', component: InspectionsView },
  { path: '/admin', name: 'admin', component: AdminView },
]

export const createAppRouter = (history: RouterHistory = createWebHistory()) => {
  return createRouter({
    history,
    routes: APP_ROUTES,
  })
}
