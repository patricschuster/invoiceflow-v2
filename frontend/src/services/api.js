import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Invoice API endpoints
export const invoiceAPI = {
  // Get all invoices
  getInvoices(status = null, skip = 0, limit = 100) {
    const params = { skip, limit }
    if (status) {
      params.status = status
    }
    return api.get('/invoices/', { params })
  },

  // Get invoice by ID
  getInvoice(id) {
    return api.get(`/invoices/${id}`)
  },

  // Get invoice statistics
  getStats() {
    return api.get('/invoices/stats')
  },

  // Create invoice
  createInvoice(data) {
    return api.post('/invoices/', data)
  },

  // Update invoice
  updateInvoice(id, data) {
    return api.patch(`/invoices/${id}`, data)
  },

  // Approve invoice
  approveInvoice(id, data) {
    return api.post(`/invoices/${id}/approve`, data)
  },

  // Reject invoice
  rejectInvoice(id, data) {
    return api.post(`/invoices/${id}/reject`, data)
  },

  // Delete invoice
  deleteInvoice(id) {
    return api.delete(`/invoices/${id}`)
  },

  // Delete all invoices
  deleteAllInvoices() {
    return api.delete('/invoices/bulk')
  },

  // Upload invoice file
  uploadInvoice(file, options = {}) {
    const formData = new FormData()
    formData.append('file', file)

    if (options.autoExtract !== undefined) {
      formData.append('auto_extract', options.autoExtract)
    }
    if (options.invoiceType) {
      formData.append('invoice_type', options.invoiceType)
    }

    return api.post('/invoices/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: options.onProgress || null,
    })
  },

  // Get invoice file (returns blob)
  getInvoiceFile(id, disposition = 'inline') {
    return api.get(`/invoices/${id}/file`, {
      params: { disposition },
      responseType: 'blob',
    })
  },

  // Download invoice file
  downloadInvoiceFile(id, filename) {
    return this.getInvoiceFile(id, 'attachment').then(response => {
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    })
  },
}

// Health / System API
export const systemAPI = {
  checkPaperlessStatus() {
    return axios.get(`${API_URL}/api/health/paperless`)
  },
}

export default api
