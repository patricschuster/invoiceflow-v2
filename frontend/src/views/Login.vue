<template>
  <v-app>
    <v-main class="login-bg">
      <v-container class="d-flex align-center justify-center fill-height">
        <v-card width="420" elevation="8" rounded="lg">
          <!-- Header -->
          <v-card-title class="text-center pt-6 pb-2">
            <div class="d-flex flex-column align-center">
              <v-icon icon="mdi-receipt-text-outline" size="48" color="primary" class="mb-2"></v-icon>
              <span class="text-h5 font-weight-bold">Rechnungseingang</span>
              <span class="text-caption text-grey mt-1">Bitte melden Sie sich an</span>
            </div>
          </v-card-title>

          <v-card-text class="px-6 pb-4">
            <v-form ref="form" @submit.prevent="doLogin">
              <v-text-field
                v-model="username"
                label="Benutzername"
                prepend-inner-icon="mdi-account"
                variant="outlined"
                density="comfortable"
                class="mb-3"
                autofocus
                :rules="[v => !!v || 'Benutzername erforderlich']"
              ></v-text-field>

              <v-text-field
                v-model="password"
                label="Passwort"
                prepend-inner-icon="mdi-lock"
                :type="showPassword ? 'text' : 'password'"
                :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showPassword = !showPassword"
                variant="outlined"
                density="comfortable"
                class="mb-1"
                :rules="[v => !!v || 'Passwort erforderlich']"
              ></v-text-field>

              <v-alert
                v-if="errorMsg"
                type="error"
                variant="tonal"
                density="compact"
                class="mb-3"
              >
                {{ errorMsg }}
              </v-alert>

              <v-btn
                type="submit"
                color="primary"
                block
                size="large"
                :loading="loading"
                class="mt-2"
              >
                Anmelden
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authService } from '@/services/auth'

const router = useRouter()
const route = useRoute()

const form = ref(null)
const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const errorMsg = ref('')

const doLogin = async () => {
  const { valid } = await form.value.validate()
  if (!valid) return

  loading.value = true
  errorMsg.value = ''

  try {
    await authService.login(username.value, password.value)
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (err) {
    const detail = err.response?.data?.detail
    errorMsg.value = detail || 'Anmeldung fehlgeschlagen'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-bg {
  background: linear-gradient(135deg, #e8eaf6 0%, #e3f2fd 100%);
}
</style>
