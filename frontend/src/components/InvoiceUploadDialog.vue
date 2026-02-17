<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon icon="mdi-upload" class="mr-2"></v-icon>
      Rechnung hochladen
      <v-spacer></v-spacer>
      <v-btn
        icon="mdi-close"
        variant="text"
        @click="emit('close')"
      ></v-btn>
    </v-card-title>

    <v-divider></v-divider>

    <v-card-text class="pa-6">
      <FileUpload
        @upload-success="handleUploadSuccess"
        @upload-error="handleUploadError"
      />
    </v-card-text>

    <v-divider v-if="uploadedInvoice"></v-divider>

    <v-card-actions v-if="uploadedInvoice">
      <v-btn
        prepend-icon="mdi-plus"
        @click="resetUpload"
      >
        Weitere Rechnung hochladen
      </v-btn>
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        prepend-icon="mdi-eye"
        :to="`/invoices/${uploadedInvoice.id}`"
        @click="emit('close')"
      >
        Rechnung ansehen
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import FileUpload from './FileUpload.vue'

// Emits
const emit = defineEmits(['close', 'upload-success'])

// State
const uploadedInvoice = ref(null)

// Methods
const handleUploadSuccess = (invoice) => {
  uploadedInvoice.value = invoice
  emit('upload-success', invoice)
}

const handleUploadError = (error) => {
  console.error('Upload error in dialog:', error)
}

const resetUpload = () => {
  uploadedInvoice.value = null
}
</script>

<style scoped>
/* Component-specific styles */
</style>
