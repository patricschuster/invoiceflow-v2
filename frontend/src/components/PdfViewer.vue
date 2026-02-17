<template>
  <v-card>
    <!-- Toolbar -->
    <v-toolbar v-if="showControls" density="compact" color="grey-lighten-4">
      <v-btn
        icon="mdi-download"
        variant="text"
        @click="downloadPdf"
        :disabled="!pdfUrl"
        title="PDF herunterladen"
      ></v-btn>

      <v-btn
        icon="mdi-rotate-right"
        variant="text"
        @click="rotate"
        :disabled="!pdfUrl"
        title="Rotieren"
      ></v-btn>

      <v-divider vertical class="mx-2"></v-divider>

      <v-btn
        icon="mdi-minus"
        variant="text"
        @click="zoomOut"
        :disabled="!pdfUrl || currentZoom <= 50"
        title="Verkleinern"
      ></v-btn>

      <span class="text-body-2 mx-2">{{ currentZoom }}%</span>

      <v-btn
        icon="mdi-plus"
        variant="text"
        @click="zoomIn"
        :disabled="!pdfUrl || currentZoom >= 200"
        title="Vergrößern"
      ></v-btn>

      <v-spacer></v-spacer>

      <v-btn
        icon="mdi-chevron-left"
        variant="text"
        @click="prevPage"
        :disabled="!pdfUrl || currentPage === 1"
        title="Vorherige Seite"
      ></v-btn>

      <span class="text-body-2 mx-2">
        Seite {{ currentPage }} / {{ totalPages }}
      </span>

      <v-btn
        icon="mdi-chevron-right"
        variant="text"
        @click="nextPage"
        :disabled="!pdfUrl || currentPage === totalPages"
        title="Nächste Seite"
      ></v-btn>
    </v-toolbar>

    <!-- PDF Container -->
    <v-card-text class="pa-0">
      <div
        class="pdf-container"
        :style="{ height: height, overflow: 'auto', backgroundColor: '#f5f5f5' }"
      >
        <!-- Loading State -->
        <div v-if="loading" class="d-flex align-center justify-center" style="height: 100%">
          <div class="text-center">
            <v-progress-circular
              indeterminate
              color="primary"
              size="64"
            ></v-progress-circular>
            <p class="mt-4 text-body-1">PDF wird geladen...</p>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="d-flex align-center justify-center" style="height: 100%">
          <v-alert
            type="error"
            variant="tonal"
            class="ma-4"
            max-width="500"
          >
            <v-alert-title>Fehler beim Laden des PDFs</v-alert-title>
            {{ error }}
          </v-alert>
        </div>

        <!-- PDF Viewer -->
        <div v-else-if="pdfUrl" class="d-flex justify-center pa-4">
          <VuePdfEmbed
            ref="pdfViewer"
            :source="pdfUrl"
            :page="currentPage"
            :rotation="rotation"
            :width="pdfWidth"
            @loaded="onPdfLoaded"
            @rendered="onPdfRendered"
            @rendering-failed="onRenderingFailed"
          />
        </div>

        <!-- No PDF State -->
        <div v-else class="d-flex align-center justify-center" style="height: 100%">
          <v-alert
            type="info"
            variant="tonal"
            class="ma-4"
          >
            Keine PDF-Datei verfügbar
          </v-alert>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import VuePdfEmbed from 'vue-pdf-embed'
import { invoiceAPI } from '@/services/api'

// Props
const props = defineProps({
  invoiceId: {
    type: Number,
    required: true
  },
  showControls: {
    type: Boolean,
    default: true
  },
  height: {
    type: String,
    default: '600px'
  }
})

// State
const pdfViewer = ref(null)
const pdfUrl = ref(null)
const loading = ref(false)
const error = ref(null)
const currentPage = ref(1)
const totalPages = ref(0)
const currentZoom = ref(100)
const rotation = ref(0)
const containerWidth = ref(800)

// Computed
const pdfWidth = computed(() => {
  return (containerWidth.value * currentZoom.value) / 100
})

// Methods
const loadPdf = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await invoiceAPI.getInvoiceFile(props.invoiceId, 'inline')

    // Create blob URL from response
    const blob = new Blob([response.data], { type: 'application/pdf' })
    pdfUrl.value = URL.createObjectURL(blob)

    console.log('PDF loaded successfully')
  } catch (err) {
    console.error('Error loading PDF:', err)

    if (err.response?.status === 404) {
      error.value = 'PDF-Datei nicht gefunden'
    } else if (err.response?.status === 403) {
      error.value = 'Zugriff verweigert'
    } else {
      error.value = 'Fehler beim Laden der PDF-Datei'
    }
  } finally {
    loading.value = false
  }
}

const downloadPdf = async () => {
  try {
    await invoiceAPI.downloadInvoiceFile(props.invoiceId, `invoice_${props.invoiceId}.pdf`)
  } catch (err) {
    console.error('Error downloading PDF:', err)
    error.value = 'Fehler beim Herunterladen der PDF-Datei'
  }
}

const zoomIn = () => {
  if (currentZoom.value < 200) {
    currentZoom.value = Math.min(200, currentZoom.value + 25)
  }
}

const zoomOut = () => {
  if (currentZoom.value > 50) {
    currentZoom.value = Math.max(50, currentZoom.value - 25)
  }
}

const rotate = () => {
  rotation.value = (rotation.value + 90) % 360
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const onPdfLoaded = (pdf) => {
  console.log('PDF loaded:', pdf)
  // Get total pages from the loaded PDF document
  if (pdf && pdf.numPages) {
    totalPages.value = pdf.numPages
    console.log(`PDF has ${totalPages.value} pages`)
  }
}

const onPdfRendered = (data) => {
  console.log('PDF rendered:', data)
  // Fallback: Get total pages from render data if not already set
  if (!totalPages.value && data && data.numPages) {
    totalPages.value = data.numPages
  }
}

const onRenderingFailed = (err) => {
  console.error('PDF rendering failed:', err)
  error.value = 'Fehler beim Rendern der PDF-Datei'
}

// Helper function for responsive sizing
const updateWidth = () => {
  const container = document.querySelector('.pdf-container')
  if (container) {
    containerWidth.value = container.clientWidth - 32 // Subtract padding
  }
}

// Lifecycle
onMounted(() => {
  loadPdf()
  updateWidth()
  window.addEventListener('resize', updateWidth)
})

onUnmounted(() => {
  // Clean up blob URL
  if (pdfUrl.value) {
    URL.revokeObjectURL(pdfUrl.value)
  }

  window.removeEventListener('resize', updateWidth)
})

// Watch for invoice ID changes
watch(() => props.invoiceId, () => {
  // Clean up old PDF URL
  if (pdfUrl.value) {
    URL.revokeObjectURL(pdfUrl.value)
    pdfUrl.value = null
  }

  // Reset state
  currentPage.value = 1
  totalPages.value = 0
  currentZoom.value = 100
  rotation.value = 0

  // Load new PDF
  loadPdf()
})
</script>

<style scoped>
.pdf-container {
  position: relative;
}

.pdf-container >>> canvas {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>
