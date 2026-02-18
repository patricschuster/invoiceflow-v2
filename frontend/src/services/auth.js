import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const TOKEN_KEY = 'invoiceflow_token'
const USER_KEY = 'invoiceflow_user'

export const authService = {
  /**
   * Login with username + password (OAuth2 form-data).
   * Stores token and user in localStorage.
   */
  async login(username, password) {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)

    const response = await axios.post(`${API_URL}/api/auth/login`, formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })

    const { access_token, user } = response.data
    localStorage.setItem(TOKEN_KEY, access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    return user
  },

  logout() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  },

  getToken() {
    return localStorage.getItem(TOKEN_KEY)
  },

  getCurrentUser() {
    try {
      const raw = localStorage.getItem(USER_KEY)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  },

  isAuthenticated() {
    return !!this.getToken()
  },

  isSuperuser() {
    const user = this.getCurrentUser()
    return user?.is_superuser === true
  },
}

export default authService
