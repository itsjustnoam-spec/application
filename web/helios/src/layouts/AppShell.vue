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

<script setup lang="ts">
import { NAVIGATION_ITEMS } from '@/config/navigation'
import { useNavigationStore } from '@/stores/navigation'

const navigationStore = useNavigationStore()
</script>
