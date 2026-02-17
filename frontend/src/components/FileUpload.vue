<template>
  <v-card>
    <v-card-text>
      <!-- Drag & Drop Zone -->
      <div
        class="upload-zone"
        :class="{ 'drag-over': isDragOver, 'uploading': uploading }"
        @dragover.prevent="isDragOver = true"
        @dragleave.prevent="isDragOver = false"
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          :accept="accept"
          style="display: none"
          @change="handleFileSelect"
        />

        <div v-if="!selectedFile && !uploading" class="text-center">
          <v-icon
            icon="mdi-cloud-upload"
            size="64"
            color="primary"
            class="mb-4"
          ></v-icon>
          <p class="text-h6 mb-2">Rechnung hochladen</p>
          <p class="text-body-2 text-grey">
            ZUGFeRD PDF oder XRechnung XML Datei hier ablegen
            <br />
            oder klicken zum Auswählen
          </p>
          <p class="text-caption text-grey mt-2">
            Maximal {{ maxSizeMB }}MB • PDF, XML
          </p>
        </div>

        <div v-else-if="selectedFile && !uploading" class="text-center">
          <v-icon
            :icon="fileIcon"
            size="64"
            :color="fileColor"
            class="mb-4"
          ></v-icon>
          <p class="text-body-1 font-weight-medium">{{ selectedFile.name }}</p>
          <p class="text-caption text-grey">{{ fileSizeFormatted }}</p>

          <v-btn
            color="error"
            variant="text"
            prepend-icon="mdi-close"
            @click.stop="clearFile"
            class="mt-2"
          >
            Entfernen
          </v-btn>
        </div>

        <div v-else class="text-center">
          <v-progress-circular
            indeterminate
            color="primary"
            size="64"
            class="mb-4"
          ></v-progress-circular>
          <p class="text-body-1">Wird hochgeladen...</p>
          <v-progress-linear
            v-if="uploadProgress > 0"
            :model-value="uploadProgress"
            color="primary"
            class="mt-4"
            height="8"
          ></v-progress-linear>
          <p v-if="uploadProgress > 0" class="text-caption mt-2">
            {{ uploadProgress }}%
          </p>
        </div>
      </div>

      <!-- Options -->
      <div v-if="!uploading" class="mt-4">
        <v-checkbox
          v-model="autoExtractData"
          label="Rechnungsdaten automatisch extrahieren (ZUGFeRD/XRechnung)"
          hide-details
          density="compact"
        ></v-checkbox>
      </div>

      <!-- Error Messages -->
      <v-alert
        v-if="errorMessage"
        type="error"
        variant="tonal"
        class="mt-4"
        closable
        @click:close="errorMessage = null"
      >
        {{ errorMessage }}
      </v-alert>

      <!-- Success Message with Extracted Data -->
      <v-alert
        v-if="successMessage"
        type="success"
        variant="tonal"
        class="mt-4"
      >
        <v-alert-title>Upload erfolgreich!</v-alert-title>
        {{ successMessage }}

        <div v-if="extractedData" class="mt-3">
          <p class="text-subtitle-2 mb-2">Extrahierte Daten:</p>
          <v-chip
            v-if="extractedData.invoice_number"
            size="small"
            class="mr-1 mb-1"
            prepend-icon="mdi-receipt"
          >
            {{ extractedData.invoice_number }}
          </v-chip>
          <v-chip
            v-if="extractedData.supplier_name"
            size="small"
            class="mr-1 mb-1"
            prepend-icon="mdi-domain"
          >
            {{ extractedData.supplier_name }}
          </v-chip>
          <v-chip
            v-if="extractedData.amount_gross"
            size="small"
            class="mr-1 mb-1"
            prepend-icon="mdi-currency-eur"
            color="success"
          >
            {{ formatCurrency(extractedData.amount_gross) }}
          </v-chip>
        </div>
      </v-alert>
    </v-card-text>

    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        prepend-icon="mdi-upload"
        :disabled="!selectedFile || uploading"
        :loading="uploading"
        @click="uploadFile"
      >
        Hochladen
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { invoiceAPI } from '@/services/api'

// Props
const props = defineProps({
  accept: {
    type: String,
    default: '.pdf,.xml'
  },
  maxSize: {
    type: Number,
    default: 52428800 // 50MB
  },
  autoExtract: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['upload-success', 'upload-error'])

// State
const fileInput = ref(null)
const selectedFile = ref(null)
const isDragOver = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const autoExtractData = ref(props.autoExtract)
const errorMessage = ref(null)
const successMessage = ref(null)
const extractedData = ref(null)

// Computed
const maxSizeMB = computed(() => Math.round(props.maxSize / 1024 / 1024))

const fileSizeFormatted = computed(() => {
  if (!selectedFile.value) return ''

  const bytes = selectedFile.value.size
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
})

const fileIcon = computed(() => {
  if (!selectedFile.value) return 'mdi-file'

  const name = selectedFile.value.name.toLowerCase()
  if (name.endsWith('.pdf')) return 'mdi-file-pdf-box'
  if (name.endsWith('.xml')) return 'mdi-file-xml-box'
  return 'mdi-file'
})

const fileColor = computed(() => {
  if (!selectedFile.value) return 'grey'

  const name = selectedFile.value.name.toLowerCase()
  if (name.endsWith('.pdf')) return 'error'
  if (name.endsWith('.xml')) return 'success'
  return 'grey'
})

// Methods
const triggerFileInput = () => {
  if (!uploading.value) {
    fileInput.value.click()
  }
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    validateAndSetFile(file)
  }
}

const handleDrop = (event) => {
  isDragOver.value = false

  const file = event.dataTransfer.files[0]
  if (file) {
    validateAndSetFile(file)
  }
}

const validateAndSetFile = (file) => {
  // Clear previous messages
  errorMessage.value = null
  successMessage.value = null
  extractedData.value = null

  // Check file size
  if (file.size > props.maxSize) {
    errorMessage.value = `Datei zu groß: ${(file.size / 1024 / 1024).toFixed(1)}MB. Maximum: ${maxSizeMB.value}MB`
    return
  }

  // Check file type
  const validExtensions = props.accept.split(',').map(ext => ext.trim().toLowerCase())
  const fileName = file.name.toLowerCase()
  const isValid = validExtensions.some(ext => fileName.endsWith(ext))

  if (!isValid) {
    errorMessage.value = `Ungültiger Dateityp. Erlaubt: ${props.accept}`
    return
  }

  selectedFile.value = file
}

const clearFile = () => {
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  errorMessage.value = null
  successMessage.value = null
  extractedData.value = null
}

const uploadFile = async () => {
  if (!selectedFile.value) return

  uploading.value = true
  uploadProgress.value = 0
  errorMessage.value = null
  successMessage.value = null

  try {
    const response = await invoiceAPI.uploadInvoice(
      selectedFile.value,
      {
        autoExtract: autoExtractData.value,
        invoiceType: 'incoming',
        onProgress: (progressEvent) => {
          uploadProgress.value = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
        }
      }
    )

    const invoice = response.data

    // Show success message
    successMessage.value = `Rechnung "${selectedFile.value.name}" wurde erfolgreich hochgeladen.`

    // Store extracted data for display
    extractedData.value = {
      invoice_number: invoice.invoice_number,
      supplier_name: invoice.supplier_name,
      amount_gross: invoice.amount_gross
    }

    // Emit success event
    emit('upload-success', invoice)

    // Clear file after short delay to show success
    setTimeout(() => {
      clearFile()
      uploadProgress.value = 0
    }, 3000)

  } catch (error) {
    console.error('Upload error:', error)

    if (error.response?.status === 400) {
      errorMessage.value = error.response.data.detail || 'Ungültige Datei'
    } else if (error.response?.status === 413) {
      errorMessage.value = 'Datei zu groß'
    } else {
      errorMessage.value = 'Fehler beim Hochladen. Bitte versuchen Sie es erneut.'
    }

    emit('upload-error', error)
  } finally {
    uploading.value = false
  }
}

const formatCurrency = (amount) => {
  if (!amount && amount !== 0) return 'N/A'
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR'
  }).format(amount)
}
</script>

<style scoped>
.upload-zone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 48px 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #fafafa;
}

.upload-zone:hover {
  border-color: #1976d2;
  background-color: #f5f5f5;
}

.upload-zone.drag-over {
  border-color: #1976d2;
  background-color: #e3f2fd;
}

.upload-zone.uploading {
  cursor: not-allowed;
  opacity: 0.7;
}
</style>
