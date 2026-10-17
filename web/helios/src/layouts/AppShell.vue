<template>
  <v-layout>
    <v-app-bar>
      <v-app-bar-nav-icon
        data-testid="toggle-drawer-button"
        @click="navigationStore.toggleDrawer"
      />
      <v-app-bar-title>FieldOps</v-app-bar-title>
    </v-app-bar>
    <v-navigation-drawer v-model="navigationStore.isDrawerOpen">
      <v-list nav>
        <v-list-item
          v-for="item in NAVIGATION_ITEMS"
          :key="item.path"
          :to="item.path"
          :title="item.title"
          :prepend-icon="item.icon"
        />
      </v-list>
    </v-navigation-drawer>
    <v-main>
      <router-view />
    </v-main>
  </v-layout>
</template>

<script lang="ts">
interface NavigationItem {
  title: string
  path: string
  icon: string
}

const NAVIGATION_ITEMS: NavigationItem[] = [
  { title: 'Dashboard', path: '/dashboard', icon: 'mdi-view-dashboard' },
  { title: 'Assets', path: '/assets', icon: 'mdi-factory' },
  { title: 'Work Orders', path: '/work-orders', icon: 'mdi-clipboard-list' },
  { title: 'Inspections', path: '/inspections', icon: 'mdi-magnify' },
  { title: 'Admin', path: '/admin', icon: 'mdi-cog' },
]
</script>

<script setup lang="ts">
import { useNavigationStore } from '@/stores/navigation'

const navigationStore = useNavigationStore()
</script>
