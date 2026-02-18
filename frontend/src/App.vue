<template>
  <v-app>
    <v-app-bar color="primary" prominent>
      <v-toolbar-title class="text-h5 font-weight-bold">
        <v-icon icon="mdi-receipt-text-outline" class="mr-2"></v-icon>
        Rechnungseingang
      </v-toolbar-title>

      <v-spacer></v-spacer>

      <!-- Account menu (only shown when logged in) -->
      <template v-if="isLoggedIn">
        <v-menu>
          <template v-slot:activator="{ props }">
            <v-btn v-bind="props" variant="text" prepend-icon="mdi-account-circle">
              {{ currentUser?.username }}
            </v-btn>
          </template>
          <v-list density="compact">
            <v-list-item
              v-if="isSuperuser"
              prepend-icon="mdi-shield-crown"
              title="Administration"
              to="/admin"
            ></v-list-item>
            <v-divider v-if="isSuperuser"></v-divider>
            <v-list-item
              prepend-icon="mdi-logout"
              title="Abmelden"
              @click="logout"
            ></v-list-item>
          </v-list>
        </v-menu>
      </template>
    </v-app-bar>

    <!-- Navigation Drawer: only visible when logged in -->
    <v-navigation-drawer v-if="isLoggedIn" permanent rail>
      <v-list>
        <v-list-item
          prepend-icon="mdi-view-dashboard"
          title="Dashboard"
          to="/"
        ></v-list-item>

        <v-list-item
          prepend-icon="mdi-clock-outline"
          title="Offene Rechnungen"
          to="/invoices/pending"
        ></v-list-item>

        <v-list-item
          prepend-icon="mdi-check-circle-outline"
          title="Freigegebene"
          to="/invoices/approved"
        ></v-list-item>

        <v-list-item
          prepend-icon="mdi-close-circle-outline"
          title="Abgelehnte"
          to="/invoices/rejected"
        ></v-list-item>

        <v-divider v-if="isSuperuser" class="my-1"></v-divider>

        <v-list-item
          v-if="isSuperuser"
          prepend-icon="mdi-shield-crown"
          title="Administration"
          to="/admin"
        ></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container fluid>
        <router-view :key="$route.fullPath"></router-view>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authService } from '@/services/auth'

const router = useRouter()
const route = useRoute()

const isLoggedIn = computed(() => {
  // Reactive: re-evaluate whenever the route changes (login/logout navigations)
  void route.path
  return authService.isAuthenticated()
})

const currentUser = computed(() => {
  void route.path
  return authService.getCurrentUser()
})

const isSuperuser = computed(() => {
  void route.path
  return authService.isSuperuser()
})

const logout = () => {
  authService.logout()
  router.push('/login')
}
</script>

<style scoped>
/* Custom styles */
</style>
