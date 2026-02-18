<template>
  <div>
    <!-- Page Header -->
    <v-row class="mb-4" align="center">
      <v-col>
        <h1 class="text-h4 font-weight-bold">
          {{ pageTitle }}
        </h1>
        <p class="text-subtitle-1 text-grey mb-0">
          Übersicht aller Rechnungen
        </p>
      </v-col>
      <v-col cols="auto" class="d-flex align-center gap-2">
        <!-- Logged-in user chip -->
        <v-chip
          prepend-icon="mdi-account-circle"
          size="small"
          variant="tonal"
          color="primary"
        >
          {{ currentUsername }}
        </v-chip>

        <!-- DMS status chip -->
        <v-tooltip :text="paperlessTooltip" location="bottom">
          <template v-slot:activator="{ props: tooltipProps }">
            <v-chip
              v-bind="tooltipProps"
              :color="paperlessStatusColor"
              :prepend-icon="paperlessStatusIcon"
              size="small"
              variant="tonal"
              @click="checkPaperless"
              style="cursor: pointer"
            >
              DMS
            </v-chip>
          </template>
        </v-tooltip>
      </v-col>
    </v-row>

    <!-- Statistics Cards -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card height="100%">
          <v-card-text>
            <div class="text-overline mb-1">Gesamt</div>
            <div class="text-h4 font-weight-bold">{{ stats.total }}</div>
            <div class="text-caption">&nbsp;</div>
            <v-progress-linear
              color="primary"
              :model-value="100"
              class="mt-2"
            ></v-progress-linear>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card height="100%">
          <v-card-text>
            <div class="text-overline mb-1">Offen</div>
            <div class="text-h4 font-weight-bold">{{ stats.pending }}</div>
            <div class="text-caption">{{ formatCurrency(stats.total_amount_pending) }}</div>
            <v-progress-linear
              color="warning"
              :model-value="stats.total ? (stats.pending / stats.total * 100) : 0"
              class="mt-2"
            ></v-progress-linear>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card height="100%">
          <v-card-text>
            <div class="text-overline mb-1">Freigegeben</div>
            <div class="text-h4 font-weight-bold">{{ stats.approved }}</div>
            <div class="text-caption">{{ formatCurrency(stats.total_amount_approved) }}</div>
            <v-progress-linear
              color="success"
              :model-value="stats.total ? (stats.approved / stats.total * 100) : 0"
              class="mt-2"
            ></v-progress-linear>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card height="100%">
          <v-card-text>
            <div class="text-overline mb-1">Abgelehnt</div>
            <div class="text-h4 font-weight-bold">{{ stats.rejected }}</div>
            <div class="text-caption">&nbsp;</div>
            <v-progress-linear
              color="error"
              :model-value="stats.total ? (stats.rejected / stats.total * 100) : 0"
              class="mt-2"
            ></v-progress-linear>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Invoices Table -->
    <v-card>
      <v-card-title>
        <v-row align="center">
          <v-col cols="12" md="6">
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              label="Suche"
              single-line
              hide-details
              clearable
              variant="outlined"
              density="compact"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="6" class="text-right">
            <v-btn
              color="success"
              prepend-icon="mdi-upload"
              @click="showUploadDialog = true"
              class="mr-2"
            >
              Rechnung hochladen
            </v-btn>
            <v-btn
              color="primary"
              prepend-icon="mdi-refresh"
              @click="loadInvoices"
              class="mr-2"
            >
              Aktualisieren
            </v-btn>
            <v-btn
              color="error"
              prepend-icon="mdi-delete-sweep"
              @click="showDeleteAllDialog = true"
              :disabled="invoices.length === 0"
            >
              Alle löschen
            </v-btn>
          </v-col>
        </v-row>
      </v-card-title>

      <v-tabs v-model="activeTab" color="primary">
        <v-tab value="all">Alle</v-tab>
        <v-tab value="pending">Offen</v-tab>
        <v-tab value="approved">Freigegeben</v-tab>
        <v-tab value="rejected">Abgelehnt</v-tab>
      </v-tabs>

      <v-data-table
        :headers="headers"
        :items="filteredInvoices"
        :search="search"
        :loading="loading"
        class="elevation-0"
        item-value="id"
      >
        <template v-slot:item.invoice_number="{ item }">
          <router-link
            :to="`/invoices/${item.id}`"
            class="text-decoration-none text-primary font-weight-medium"
          >
            {{ item.invoice_number || 'N/A' }}
          </router-link>
        </template>

        <template v-slot:item.invoice_date="{ item }">
          {{ formatDate(item.invoice_date) }}
        </template>

        <template v-slot:item.amount_gross="{ item }">
          {{ formatCurrency(item.amount_gross) }}
        </template>

        <template v-slot:item.status="{ item }">
          <v-chip
            :color="getStatusColor(item.status)"
            size="small"
            variant="flat"
          >
            {{ getStatusText(item.status) }}
          </v-chip>
        </template>

        <template v-slot:item.actions="{ item }">
          <v-btn
            icon="mdi-eye"
            size="small"
            variant="text"
            :to="`/invoices/${item.id}`"
            title="Ansehen"
          ></v-btn>
          <v-btn
            icon="mdi-delete"
            size="small"
            variant="text"
            color="error"
            @click="confirmDelete(item)"
            title="Löschen"
          ></v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Upload Dialog -->
    <v-dialog v-model="showUploadDialog" max-width="700">
      <InvoiceUploadDialog
        @upload-success="handleUploadSuccess"
        @close="showUploadDialog = false"
      />
    </v-dialog>

    <!-- Delete Single Invoice Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6">Rechnung löschen?</v-card-title>
        <v-card-text>
          Möchten Sie die Rechnung <strong>{{ invoiceToDelete?.invoice_number || 'N/A' }}</strong> wirklich löschen?
          <br/>
          Diese Aktion kann nicht rückgängig gemacht werden.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showDeleteDialog = false">Abbrechen</v-btn>
          <v-btn
            color="error"
            @click="deleteInvoice"
            :loading="deleting"
          >
            Löschen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete All Invoices Dialog -->
    <v-dialog v-model="showDeleteAllDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6">Alle Rechnungen löschen?</v-card-title>
        <v-card-text>
          Möchten Sie wirklich <strong>{{ invoices.length }} Rechnungen</strong> löschen?
          <br/>
          <span class="text-error font-weight-bold">Diese Aktion kann nicht rückgängig gemacht werden!</span>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showDeleteAllDialog = false">Abbrechen</v-btn>
          <v-btn
            color="error"
            @click="deleteAllInvoices"
            :loading="deleting"
          >
            Alle löschen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { invoiceAPI, systemAPI } from '@/services/api'
import { authService } from '@/services/auth'
import InvoiceUploadDialog from '@/components/InvoiceUploadDialog.vue'

const currentUsername = computed(() => authService.getCurrentUser()?.username || '')

const props = defineProps({
  statusFilter: {
    type: String,
    default: null
  }
})

const route = useRoute()

const invoices = ref([])
const stats = ref({
  total: 0,
  pending: 0,
  approved: 0,
  rejected: 0,
  total_amount_pending: 0,
  total_amount_approved: 0
})
const loading = ref(false)
const search = ref('')
const activeTab = ref(props.statusFilter || 'all')
const showUploadDialog = ref(false)
const showDeleteDialog = ref(false)
const showDeleteAllDialog = ref(false)
const invoiceToDelete = ref(null)
const deleting = ref(false)

// Paperless-ngx connection status
const paperlessStatus = ref(null) // null = loading, true = ok, false = error
const paperlessUrl = ref('')
const paperlessError = ref('')

const paperlessStatusColor = computed(() => {
  if (paperlessStatus.value === null) return 'grey'
  return paperlessStatus.value ? 'success' : 'error'
})

const paperlessStatusIcon = computed(() => {
  if (paperlessStatus.value === null) return 'mdi-cloud-question'
  return paperlessStatus.value ? 'mdi-cloud-check' : 'mdi-cloud-off'
})

const paperlessTooltip = computed(() => {
  if (paperlessStatus.value === null) return 'Verbindungsstatus wird geprüft...'
  if (paperlessStatus.value) return `Verbunden mit ${paperlessUrl.value}`
  return `Nicht erreichbar: ${paperlessError.value || paperlessUrl.value}`
})

const checkPaperless = async () => {
  paperlessStatus.value = null
  try {
    const { data } = await systemAPI.checkPaperlessStatus()
    paperlessUrl.value = data.url
    paperlessStatus.value = data.connected
    paperlessError.value = data.error || ''
  } catch {
    paperlessStatus.value = false
    paperlessError.value = 'API nicht erreichbar'
  }
}

const headers = [
  { title: 'Rechnungsnr.', key: 'invoice_number', sortable: true },
  { title: 'Datum', key: 'invoice_date', sortable: true },
  { title: 'Lieferant', key: 'supplier_name', sortable: true },
  { title: 'Betrag', key: 'amount_gross', sortable: true },
  { title: 'Kostenstelle', key: 'cost_center', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false, align: 'center' }
]

const pageTitle = computed(() => {
  if (props.statusFilter === 'pending') return 'Offene Rechnungen'
  if (props.statusFilter === 'approved') return 'Freigegebene Rechnungen'
  if (props.statusFilter === 'rejected') return 'Abgelehnte Rechnungen'
  return 'Dashboard'
})

const filteredInvoices = computed(() => {
  if (activeTab.value === 'all') return invoices.value
  return invoices.value.filter(inv => inv.status === activeTab.value)
})

const loadInvoices = async () => {
  console.log('[Dashboard] loadInvoices() called')
  loading.value = true
  try {
    const [invoicesRes, statsRes] = await Promise.all([
      invoiceAPI.getInvoices(),
      invoiceAPI.getStats()
    ])
    invoices.value = invoicesRes.data
    stats.value = statsRes.data
    console.log('[Dashboard] Loaded', invoices.value.length, 'invoices')
    console.log('[Dashboard] Stats:', stats.value)
  } catch (error) {
    console.error('[Dashboard] Error loading invoices:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString('de-DE')
}

const formatCurrency = (amount) => {
  if (!amount && amount !== 0) return 'N/A'
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR'
  }).format(amount)
}

const getStatusColor = (status) => {
  switch (status) {
    case 'pending': return 'warning'
    case 'approved': return 'success'
    case 'rejected': return 'error'
    default: return 'grey'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'pending': return 'Offen'
    case 'approved': return 'Freigegeben'
    case 'rejected': return 'Abgelehnt'
    default: return status
  }
}

const handleUploadSuccess = (invoice) => {
  // Refresh invoice list after successful upload
  loadInvoices()
}

const confirmDelete = (invoice) => {
  invoiceToDelete.value = invoice
  showDeleteDialog.value = true
}

const deleteInvoice = async () => {
  if (!invoiceToDelete.value) return

  deleting.value = true
  try {
    await invoiceAPI.deleteInvoice(invoiceToDelete.value.id)
    console.log('[Dashboard] Invoice deleted:', invoiceToDelete.value.id)
    showDeleteDialog.value = false
    invoiceToDelete.value = null
    // Refresh invoice list
    loadInvoices()
  } catch (error) {
    console.error('[Dashboard] Error deleting invoice:', error)
    alert('Fehler beim Löschen der Rechnung')
  } finally {
    deleting.value = false
  }
}

const deleteAllInvoices = async () => {
  deleting.value = true
  try {
    const response = await invoiceAPI.deleteAllInvoices()
    console.log('[Dashboard] All invoices deleted:', response.data)
    showDeleteAllDialog.value = false
    // Refresh invoice list
    loadInvoices()
  } catch (error) {
    console.error('[Dashboard] Error deleting all invoices:', error)
    alert('Fehler beim Löschen aller Rechnungen')
  } finally {
    deleting.value = false
  }
}

watch(() => props.statusFilter, (newValue) => {
  console.log('[Dashboard] statusFilter changed to:', newValue)
  activeTab.value = newValue || 'all'
})

// Watch route changes to reload data when navigating between dashboard views
watch(() => route.path, (newPath) => {
  console.log('[Dashboard] Route path changed to:', newPath)
  loadInvoices()
})

onMounted(() => {
  console.log('[Dashboard] Component mounted, route:', route.path)
  loadInvoices()
  checkPaperless()
})
</script>

<style scoped>
/* Custom styles */
</style>
