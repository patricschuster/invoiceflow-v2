<template>
  <v-app>
    <v-app-bar color="primary" prominent>
      <v-app-bar-nav-icon variant="text"></v-app-bar-nav-icon>

      <v-toolbar-title class="text-h5 font-weight-bold">
        <v-icon icon="mdi-receipt-text-outline" class="mr-2"></v-icon>
        InvoiceFlow
      </v-toolbar-title>

      <v-spacer></v-spacer>

      <v-btn icon="mdi-cog" variant="text"></v-btn>
      <v-btn icon="mdi-account-circle" variant="text"></v-btn>
    </v-app-bar>

    <v-navigation-drawer permanent>
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

        <v-divider class="my-2"></v-divider>

        <v-list-item
          prepend-icon="mdi-file-upload-outline"
          title="Import"
        ></v-list-item>

        <v-list-item
          prepend-icon="mdi-download-outline"
          title="Export"
        ></v-list-item>

        <v-list-item
          prepend-icon="mdi-chart-bar"
          title="Berichte"
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
// App component
</script>

<style scoped>
/* Custom styles */
</style>
