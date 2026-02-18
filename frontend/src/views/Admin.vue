<template>
  <div>
    <v-row class="mb-3" align="center">
      <v-col>
        <h2 class="text-h6 font-weight-bold">
          <v-icon icon="mdi-shield-crown" class="mr-2" color="primary"></v-icon>
          Administration
        </h2>
      </v-col>
    </v-row>

    <v-tabs v-model="tab" color="primary" class="mb-4">
      <v-tab value="settings">
        <v-icon start icon="mdi-cog"></v-icon>
        Konfiguration
      </v-tab>
      <v-tab value="users">
        <v-icon start icon="mdi-account-multiple"></v-icon>
        Benutzer
      </v-tab>
    </v-tabs>

    <v-tabs-window v-model="tab">

      <!-- ── Settings Tab ── -->
      <v-tabs-window-item value="settings">
        <v-card>
          <v-card-title class="py-3 px-4">
            <v-icon icon="mdi-paperclip" class="mr-2" size="small"></v-icon>
            Paperless-ngx Integration
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text class="pa-4">
            <v-alert
              type="info"
              variant="tonal"
              density="compact"
              class="mb-4"
              text="Änderungen werden sofort aktiv – ein Neustart ist nicht erforderlich."
            ></v-alert>

            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="settingsForm.PAPERLESS_URL"
                  label="Paperless URL"
                  placeholder="http://192.168.1.100:8000"
                  prepend-inner-icon="mdi-web"
                  variant="outlined"
                  density="comfortable"
                  hint="URL der Paperless-ngx Instanz (z.B. http://192.168.1.100:8000)"
                  persistent-hint
                  class="mb-4"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="settingsForm.PAPERLESS_TOKEN"
                  label="API-Token"
                  :type="showToken ? 'text' : 'password'"
                  :append-inner-icon="showToken ? 'mdi-eye-off' : 'mdi-eye'"
                  @click:append-inner="showToken = !showToken"
                  prepend-inner-icon="mdi-key"
                  variant="outlined"
                  density="comfortable"
                  hint="Token aus Paperless: Mein Konto → API-Token"
                  persistent-hint
                  class="mb-4"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-alert
              v-if="settingsSaveMsg"
              :type="settingsSaveOk ? 'success' : 'error'"
              variant="tonal"
              density="compact"
              class="mb-4"
            >{{ settingsSaveMsg }}</v-alert>

            <div class="d-flex gap-3">
              <v-btn
                color="primary"
                prepend-icon="mdi-content-save"
                @click="saveSettings"
                :loading="savingSettings"
              >
                Speichern
              </v-btn>
              <v-btn
                variant="outlined"
                prepend-icon="mdi-cloud-check"
                @click="testConnection"
                :loading="testingConnection"
              >
                Verbindung testen
              </v-btn>
            </div>

            <v-alert
              v-if="connectionResult !== null"
              :type="connectionResult.connected ? 'success' : 'error'"
              variant="tonal"
              density="compact"
              class="mt-3"
            >
              <template v-if="connectionResult.connected">
                Verbunden mit <strong>{{ connectionResult.url }}</strong>
              </template>
              <template v-else>
                Keine Verbindung zu {{ connectionResult.url }}: {{ connectionResult.error }}
              </template>
            </v-alert>
          </v-card-text>
        </v-card>
      </v-tabs-window-item>

      <!-- ── Users Tab ── -->
      <v-tabs-window-item value="users">
        <v-card>
          <v-card-title class="py-3 px-4 d-flex align-center">
            <span>Benutzerverwaltung</span>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              prepend-icon="mdi-account-plus"
              size="small"
              @click="openCreateDialog"
            >
              Neuer Benutzer
            </v-btn>
          </v-card-title>
          <v-divider></v-divider>
          <v-data-table
            :headers="userHeaders"
            :items="users"
            :loading="loadingUsers"
            item-value="id"
          >
            <template v-slot:item.is_superuser="{ item }">
              <v-chip
                :color="item.is_superuser ? 'primary' : 'default'"
                size="x-small"
                variant="tonal"
              >
                {{ item.is_superuser ? 'Admin' : 'Benutzer' }}
              </v-chip>
            </template>
            <template v-slot:item.is_active="{ item }">
              <v-chip
                :color="item.is_active ? 'success' : 'error'"
                size="x-small"
                variant="tonal"
              >
                {{ item.is_active ? 'Aktiv' : 'Inaktiv' }}
              </v-chip>
            </template>
            <template v-slot:item.created_at="{ item }">
              {{ formatDate(item.created_at) }}
            </template>
            <template v-slot:item.actions="{ item }">
              <v-btn icon="mdi-pencil" size="x-small" variant="text" @click="openEditDialog(item)"></v-btn>
              <v-btn
                icon="mdi-delete"
                size="x-small"
                variant="text"
                color="error"
                :disabled="item.username === 'admin'"
                @click="confirmDeleteUser(item)"
              ></v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-tabs-window-item>

    </v-tabs-window>

    <!-- Create/Edit User Dialog -->
    <v-dialog v-model="userDialog" max-width="460" persistent>
      <v-card>
        <v-card-title>{{ editingUser ? 'Benutzer bearbeiten' : 'Neuer Benutzer' }}</v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <v-form ref="userForm">
            <v-text-field
              v-model="userFormData.username"
              label="Benutzername"
              variant="outlined"
              density="comfortable"
              class="mb-3"
              :rules="[v => !!v || 'Pflichtfeld']"
            ></v-text-field>
            <v-text-field
              v-model="userFormData.password"
              :label="editingUser ? 'Neues Passwort (leer = unverändert)' : 'Passwort'"
              :type="showNewPw ? 'text' : 'password'"
              :append-inner-icon="showNewPw ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showNewPw = !showNewPw"
              variant="outlined"
              density="comfortable"
              class="mb-3"
              :rules="editingUser ? [] : [v => !!v || 'Pflichtfeld']"
            ></v-text-field>
            <v-switch
              v-model="userFormData.is_superuser"
              label="Administrator"
              color="primary"
              density="comfortable"
              class="mb-1"
            ></v-switch>
            <v-switch
              v-model="userFormData.is_active"
              label="Aktiv"
              color="success"
              density="comfortable"
            ></v-switch>
          </v-form>
          <v-alert v-if="userDialogError" type="error" variant="tonal" density="compact" class="mt-2">
            {{ userDialogError }}
          </v-alert>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="userDialog = false">Abbrechen</v-btn>
          <v-btn color="primary" @click="saveUser" :loading="savingUser">Speichern</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirm Dialog -->
    <v-dialog v-model="deleteDialog" max-width="380">
      <v-card>
        <v-card-title>Benutzer löschen</v-card-title>
        <v-card-text>
          Soll der Benutzer <strong>{{ deletingUser?.username }}</strong> wirklich gelöscht werden?
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="deleteDialog = false">Abbrechen</v-btn>
          <v-btn color="error" @click="deleteUser" :loading="deletingUserLoading">Löschen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { authService } from '@/services/auth'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function apiHeaders() {
  return { Authorization: `Bearer ${authService.getToken()}` }
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
const tab = ref('settings')

// ── Settings ──────────────────────────────────────────────────────────────────
const settingsForm = ref({ PAPERLESS_URL: '', PAPERLESS_TOKEN: '' })
const showToken = ref(false)
const savingSettings = ref(false)
const settingsSaveMsg = ref('')
const settingsSaveOk = ref(true)
const testingConnection = ref(false)
const connectionResult = ref(null)

const loadSettings = async () => {
  try {
    const { data } = await axios.get(`${API_URL}/api/admin/settings`, { headers: apiHeaders() })
    data.forEach(s => {
      if (s.key in settingsForm.value) settingsForm.value[s.key] = s.value || ''
    })
  } catch (e) {
    console.error('Settings laden fehlgeschlagen', e)
  }
}

const saveSettings = async () => {
  savingSettings.value = true
  settingsSaveMsg.value = ''
  try {
    for (const [key, value] of Object.entries(settingsForm.value)) {
      await axios.put(
        `${API_URL}/api/admin/settings/${key}`,
        { value },
        { headers: apiHeaders() }
      )
    }
    settingsSaveOk.value = true
    settingsSaveMsg.value = 'Einstellungen gespeichert.'
  } catch (e) {
    settingsSaveOk.value = false
    settingsSaveMsg.value = 'Fehler beim Speichern: ' + (e.response?.data?.detail || e.message)
  } finally {
    savingSettings.value = false
  }
}

const testConnection = async () => {
  testingConnection.value = true
  connectionResult.value = null
  try {
    // Save first, then test
    await saveSettings()
    const { data } = await axios.get(`${API_URL}/api/health/paperless`)
    connectionResult.value = data
  } catch {
    connectionResult.value = { connected: false, url: settingsForm.value.PAPERLESS_URL, error: 'API-Fehler' }
  } finally {
    testingConnection.value = false
  }
}

// ── Users ─────────────────────────────────────────────────────────────────────
const users = ref([])
const loadingUsers = ref(false)
const userHeaders = [
  { title: 'Benutzername', key: 'username' },
  { title: 'Rolle', key: 'is_superuser', sortable: false },
  { title: 'Status', key: 'is_active', sortable: false },
  { title: 'Erstellt', key: 'created_at' },
  { title: '', key: 'actions', sortable: false, align: 'end' },
]

const userDialog = ref(false)
const editingUser = ref(null)
const userForm = ref(null)
const userFormData = ref({ username: '', password: '', is_superuser: false, is_active: true })
const showNewPw = ref(false)
const savingUser = ref(false)
const userDialogError = ref('')

const deleteDialog = ref(false)
const deletingUser = ref(null)
const deletingUserLoading = ref(false)

const loadUsers = async () => {
  loadingUsers.value = true
  try {
    const { data } = await axios.get(`${API_URL}/api/admin/users`, { headers: apiHeaders() })
    users.value = data
  } catch (e) {
    console.error('Benutzer laden fehlgeschlagen', e)
  } finally {
    loadingUsers.value = false
  }
}

const openCreateDialog = () => {
  editingUser.value = null
  userFormData.value = { username: '', password: '', is_superuser: false, is_active: true }
  userDialogError.value = ''
  showNewPw.value = false
  userDialog.value = true
}

const openEditDialog = (user) => {
  editingUser.value = user
  userFormData.value = {
    username: user.username,
    password: '',
    is_superuser: user.is_superuser,
    is_active: user.is_active,
  }
  userDialogError.value = ''
  showNewPw.value = false
  userDialog.value = true
}

const saveUser = async () => {
  const { valid } = await userForm.value.validate()
  if (!valid) return

  savingUser.value = true
  userDialogError.value = ''
  try {
    const payload = { ...userFormData.value }
    if (editingUser.value && !payload.password) delete payload.password

    if (editingUser.value) {
      await axios.put(`${API_URL}/api/admin/users/${editingUser.value.id}`, payload, { headers: apiHeaders() })
    } else {
      await axios.post(`${API_URL}/api/admin/users`, payload, { headers: apiHeaders() })
    }
    userDialog.value = false
    loadUsers()
  } catch (e) {
    userDialogError.value = e.response?.data?.detail || 'Speichern fehlgeschlagen'
  } finally {
    savingUser.value = false
  }
}

const confirmDeleteUser = (user) => {
  deletingUser.value = user
  deleteDialog.value = true
}

const deleteUser = async () => {
  deletingUserLoading.value = true
  try {
    await axios.delete(`${API_URL}/api/admin/users/${deletingUser.value.id}`, { headers: apiHeaders() })
    deleteDialog.value = false
    loadUsers()
  } catch (e) {
    console.error('Löschen fehlgeschlagen', e)
  } finally {
    deletingUserLoading.value = false
  }
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('de-DE')
}

onMounted(() => {
  loadSettings()
  loadUsers()
})
</script>
