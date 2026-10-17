<template>
  <v-container>
    <h1 class="text-center text-2xl font-semibold">Admin</h1>
    <v-tabs class="mb-4" color="primary" align-tabs="center">
      <v-tab to="/admin/sites" data-testid="admin-sites-tab">Sites</v-tab>
      <v-tab to="/admin/asset-types" data-testid="admin-asset-types-tab">Asset types</v-tab>
    </v-tabs>
    <router-view />
  </v-container>
</template>
