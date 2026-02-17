<template>
  <div v-if="invoice">
    <!-- Header -->
    <v-row class="mb-2">
      <v-col>
        <v-btn
          prepend-icon="mdi-arrow-left"
          variant="text"
          @click="$router.back()"
        >
          Zurück
        </v-btn>
      </v-col>
    </v-row>

    <!-- 2-Spalten Layout: 70% PDF | 30% Details -->
    <div class="detail-layout">
      <!-- Linke Spalte: PDF Vorschau (80%) -->
      <div class="detail-col-pdf">
        <v-card class="fill-height">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-file-pdf-box" class="mr-2"></v-icon>
            Dokument Vorschau
          </v-card-title>
          <v-card-text class="pa-0">
            <PdfViewer
              v-if="isPdf"
              :invoice-id="invoice.id"
              height="calc(100vh - 140px)"
            />
            <div v-else class="pa-4">
              <v-alert type="info" variant="tonal">
                <v-alert-title>XML-Datei</v-alert-title>
                Keine PDF-Vorschau verfügbar für XML-Dateien.
                <template v-slot:append>
                  <v-btn
                    variant="text"
                    prepend-icon="mdi-download"
                    @click="downloadFile"
                  >
                    Download
                  </v-btn>
                </template>
              </v-alert>
            </div>
          </v-card-text>
        </v-card>
      </div>

      <!-- Rechte Spalte: Details + Aktionen + Metadaten (20%) -->
      <div class="detail-col-sidebar">

        <!-- Rechnungsdetails -->
        <v-card class="mb-3">
          <v-card-title class="d-flex align-center py-2 px-3">
            <v-icon icon="mdi-receipt-text" size="small" class="mr-2"></v-icon>
            <span class="text-body-1 font-weight-bold">Rechnungsdetails</span>
            <v-spacer></v-spacer>
            <v-chip
              :color="getStatusColor(invoice.status)"
              variant="flat"
              size="small"
            >
              {{ getStatusText(invoice.status) }}
            </v-chip>
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text class="pa-3">
            <div class="detail-row">
              <div class="text-caption text-grey">Rechnungsnummer</div>
              <div class="text-body-2 font-weight-medium">{{ invoice.invoice_number || 'N/A' }}</div>
            </div>
            <div class="detail-row">
              <div class="text-caption text-grey">Rechnungsdatum</div>
              <div class="text-body-2">{{ formatDate(invoice.invoice_date) }}</div>
            </div>
            <div class="detail-row">
              <div class="text-caption text-grey">Fälligkeitsdatum</div>
              <div class="text-body-2">{{ formatDate(invoice.due_date) }}</div>
            </div>
            <v-divider class="my-2"></v-divider>
            <div class="detail-row">
              <div class="text-caption text-grey">Lieferant</div>
              <div class="text-body-2 font-weight-medium">{{ invoice.supplier_name || 'N/A' }}</div>
            </div>
            <div class="detail-row">
              <div class="text-caption text-grey">Lieferanten-ID</div>
              <div class="text-body-2">{{ invoice.supplier_id || 'N/A' }}</div>
            </div>
            <v-divider class="my-2"></v-divider>
            <div class="detail-row">
              <div class="text-caption text-grey">Nettobetrag</div>
              <div class="text-body-2">{{ formatCurrency(invoice.amount_net) }}</div>
            </div>
            <div class="detail-row">
              <div class="text-caption text-grey">MwSt.</div>
              <div class="text-body-2">{{ formatCurrency(invoice.amount_vat) }}</div>
            </div>
            <div class="detail-row">
              <div class="text-caption text-grey">Bruttobetrag</div>
              <div class="text-body-2 font-weight-bold">{{ formatCurrency(invoice.amount_gross) }}</div>
            </div>
            <div class="detail-row">
              <div class="text-caption text-grey">Währung</div>
              <div class="text-body-2">{{ invoice.currency }}</div>
            </div>
            <v-divider class="my-2"></v-divider>
            <div class="detail-row">
              <div class="text-caption text-grey">Dateiname</div>
              <div class="text-body-2 text-truncate">{{ invoice.filename }}</div>
            </div>
          </v-card-text>
        </v-card>

        <!-- Freigabe- / Ablehnungs-Information -->
        <v-card v-if="invoice.status !== 'pending'" class="mb-3">
          <v-card-title class="py-2 px-3">
            <v-icon
              :icon="invoice.status === 'approved' ? 'mdi-check-circle' : 'mdi-close-circle'"
              :color="invoice.status === 'approved' ? 'success' : 'error'"
              size="small"
              class="mr-2"
            ></v-icon>
            <span class="text-body-1 font-weight-bold">
              {{ invoice.status === 'approved' ? 'Freigabe-Information' : 'Ablehnungs-Information' }}
            </span>
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text class="pa-3">
            <template v-if="invoice.status === 'approved'">
              <div class="detail-row">
                <div class="text-caption text-grey">Freigegeben von</div>
                <div class="text-body-2">{{ invoice.approved_by }}</div>
              </div>
              <div class="detail-row">
                <div class="text-caption text-grey">Freigegeben am</div>
                <div class="text-body-2">{{ formatDateTime(invoice.approved_at) }}</div>
              </div>
            </template>
            <template v-if="invoice.status === 'rejected'">
              <div class="detail-row">
                <div class="text-caption text-grey">Ablehnungsgrund</div>
                <div class="text-body-2">{{ invoice.rejection_reason }}</div>
              </div>
            </template>
          </v-card-text>
        </v-card>

        <!-- Freigabe-Aktionen -->
        <v-card v-if="invoice.status === 'pending'" class="mb-3">
          <v-card-title class="py-2 px-3">
            <v-icon icon="mdi-lightning-bolt" size="small" class="mr-2"></v-icon>
            <span class="text-body-1 font-weight-bold">Aktionen</span>
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text class="pa-3">
            <v-form ref="approvalForm">
              <!-- Klappbereich: optionale Felder -->
              <v-expansion-panels variant="accordion" class="mb-3">
                <v-expansion-panel>
                  <v-expansion-panel-title class="text-body-2 py-2">
                    Kostenstelle, Projekt, Tags &amp; Kommentar
                  </v-expansion-panel-title>
                  <v-expansion-panel-text class="pt-2">
                    <v-text-field
                      v-model="approvalData.cost_center"
                      label="Kostenstelle"
                      variant="outlined"
                      density="compact"
                      class="mb-2"
                    ></v-text-field>
                    <v-text-field
                      v-model="approvalData.project"
                      label="Projekt"
                      variant="outlined"
                      density="compact"
                      class="mb-2"
                    ></v-text-field>
                    <v-combobox
                      v-model="approvalData.tags"
                      label="Tags"
                      variant="outlined"
                      density="compact"
                      multiple
                      chips
                      closable-chips
                      class="mb-2"
                    ></v-combobox>
                    <v-textarea
                      v-model="approvalData.comment"
                      label="Kommentar"
                      variant="outlined"
                      density="compact"
                      rows="2"
                    ></v-textarea>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>

              <v-btn
                color="success"
                prepend-icon="mdi-check"
                block
                class="mb-2"
                @click="approveInvoice"
                :loading="approving"
              >
                Freigeben
              </v-btn>
              <v-btn
                color="error"
                prepend-icon="mdi-close"
                block
                variant="outlined"
                @click="showRejectDialog = true"
              >
                Ablehnen
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>

        <!-- Metadaten -->
        <v-expansion-panels variant="accordion">
          <v-expansion-panel>
            <v-expansion-panel-title class="py-2 px-3">
              <v-icon icon="mdi-information" size="small" class="mr-2"></v-icon>
              <span class="text-body-2 font-weight-bold">Metadaten</span>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <div class="detail-row mt-2">
                <div class="text-caption text-grey">Kostenstelle</div>
                <div class="text-body-2">{{ invoice.cost_center || 'Nicht zugewiesen' }}</div>
              </div>
              <div class="detail-row">
                <div class="text-caption text-grey">Projekt</div>
                <div class="text-body-2">{{ invoice.project || 'Nicht zugewiesen' }}</div>
              </div>
              <div class="detail-row">
                <div class="text-caption text-grey">Tags</div>
                <div v-if="invoice.tags && invoice.tags.length">
                  <v-chip
                    v-for="tag in invoice.tags"
                    :key="tag"
                    size="x-small"
                    class="mr-1 mb-1"
                  >{{ tag }}</v-chip>
                </div>
                <div v-else class="text-body-2">Keine Tags</div>
              </div>
              <div v-if="invoice.comment" class="detail-row">
                <div class="text-caption text-grey">Kommentar</div>
                <div class="text-body-2">{{ invoice.comment }}</div>
              </div>
              <v-divider class="my-2"></v-divider>
              <div class="detail-row">
                <div class="text-caption text-grey">Erstellt am</div>
                <div class="text-caption">{{ formatDateTime(invoice.created_at) }}</div>
              </div>
              <div class="detail-row">
                <div class="text-caption text-grey">Aktualisiert am</div>
                <div class="text-caption">{{ formatDateTime(invoice.updated_at) }}</div>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>

      </div>
    </div>

    <!-- Reject Dialog -->
    <v-dialog v-model="showRejectDialog" max-width="500">
      <v-card>
        <v-card-title>Rechnung ablehnen</v-card-title>
        <v-card-text>
          <v-textarea
            v-model="rejectionReason"
            label="Ablehnungsgrund"
            variant="outlined"
            rows="4"
            required
          ></v-textarea>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showRejectDialog = false">Abbrechen</v-btn>
          <v-btn
            color="error"
            @click="rejectInvoice"
            :loading="rejecting"
            :disabled="!rejectionReason"
          >
            Ablehnen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { invoiceAPI } from '@/services/api'
import PdfViewer from '@/components/PdfViewer.vue'

const route = useRoute()
const router = useRouter()

const invoice = ref(null)
const approvalData = ref({
  approved_by: 'admin', // TODO: Get from auth
  cost_center: '',
  project: '',
  tags: [],
  comment: ''
})
const approving = ref(false)
const rejecting = ref(false)
const showRejectDialog = ref(false)
const rejectionReason = ref('')

// Computed
const isPdf = computed(() => {
  return invoice.value && invoice.value.file_path && invoice.value.file_path.toLowerCase().endsWith('.pdf')
})

const loadInvoice = async () => {
  try {
    const response = await invoiceAPI.getInvoice(route.params.id)
    invoice.value = response.data

    // Pre-fill form with existing data
    if (invoice.value.cost_center) approvalData.value.cost_center = invoice.value.cost_center
    if (invoice.value.project) approvalData.value.project = invoice.value.project
    if (invoice.value.tags) approvalData.value.tags = invoice.value.tags
    if (invoice.value.comment) approvalData.value.comment = invoice.value.comment
  } catch (error) {
    console.error('Error loading invoice:', error)
  }
}

const approveInvoice = async () => {
  approving.value = true
  try {
    await invoiceAPI.approveInvoice(invoice.value.id, approvalData.value)
    await loadInvoice() // Reload to get updated data
  } catch (error) {
    console.error('Error approving invoice:', error)
  } finally {
    approving.value = false
  }
}

const rejectInvoice = async () => {
  rejecting.value = true
  try {
    await invoiceAPI.rejectInvoice(invoice.value.id, {
      rejection_reason: rejectionReason.value,
      rejected_by: 'admin' // TODO: Get from auth
    })
    showRejectDialog.value = false
    await loadInvoice() // Reload to get updated data
  } catch (error) {
    console.error('Error rejecting invoice:', error)
  } finally {
    rejecting.value = false
  }
}

const formatDate = (date) => {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString('de-DE')
}

const formatDateTime = (date) => {
  if (!date) return 'N/A'
  return new Date(date).toLocaleString('de-DE')
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

const downloadFile = async () => {
  if (!invoice.value) return

  try {
    await invoiceAPI.downloadInvoiceFile(invoice.value.id, invoice.value.filename)
  } catch (error) {
    console.error('Error downloading file:', error)
  }
}

// Watch route params to reload invoice when navigating between invoices
watch(() => route.params.id, (newId) => {
  if (newId) {
    loadInvoice()
  }
})

onMounted(() => {
  loadInvoice()
})
</script>

<style scoped>
.detail-layout {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.detail-col-pdf {
  flex: 0 0 70%;
  min-width: 0;
}

.detail-col-sidebar {
  flex: 0 0 calc(30% - 12px);
  min-width: 0;
  overflow-y: auto;
  max-height: calc(100vh - 120px);
}

.detail-row {
  margin-bottom: 8px;
}
</style>
