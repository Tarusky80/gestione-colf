<template>
  <div class="login-page">
    <div class="login-form">
      <div class="login-header">Accedi</div>

      <div v-if="errore" class="login-error mb-4">
        {{ errore }}
      </div>

      <form @submit.prevent="handleLogin">
        <input
          v-model="codiceFiscale"
          placeholder="Codice Fiscale"
          maxlength="16"
          required
          autofocus
          class="login-input mb-4"
          @input="codiceFiscale = codiceFiscale.toUpperCase()"
        />

        <div class="password-wrap mb-5">
          <input
            v-model="password"
            :type="mostraPw ? 'text' : 'password'"
            placeholder="Password"
            required
            class="login-input"
          />
          <button type="button" class="pw-toggle" @click="mostraPw = !mostraPw" tabindex="-1">
            {{ mostraPw ? 'Nascondi' : 'Mostra' }}
          </button>
        </div>

        <button type="submit" class="login-btn" :disabled="caricamento">
          {{ caricamento ? 'Accesso in corso...' : 'Accedi' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const codiceFiscale = ref('')
const password = ref('')
const mostraPw = ref(false)
const errore = ref('')
const caricamento = ref(false)

onMounted(() => {
  if (route.query.cf) codiceFiscale.value = route.query.cf.toUpperCase()
})

async function handleLogin() {
  if (!codiceFiscale.value || !password.value) {
    errore.value = 'Inserisci codice fiscale e password.'
    return
  }
  caricamento.value = true
  errore.value = ''
  try {
    await auth.login(codiceFiscale.value, password.value)
    router.push('/dashboard')
  } catch (err) {
    errore.value = err.response?.data?.error || 'Credenziali errate.'
  } finally {
    caricamento.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #09090B;
}
.login-form {
  width: 100%;
  max-width: 320px;
  padding: 0 24px;
}
.login-header {
  font-size: 20px;
  font-weight: 600;
  color: #E8E8ED;
  text-align: center;
  margin-bottom: 28px;
  letter-spacing: -0.01em;
}
.login-input {
  width: 100%;
  background: #131316;
  border: 1px solid #1E1E20;
  border-radius: 6px;
  color: #E8E8ED;
  font-size: 12px;
  padding: 6px 10px;
  outline: none;
  height: 32px;
  box-sizing: border-box;
}
.login-input::placeholder {
  color: #5C5F66;
}
.login-input:focus {
  border-color: #5E6AD2;
}
.password-wrap {
  position: relative;
}
.password-wrap .login-input {
  padding-right: 60px;
}
.pw-toggle {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #5C5F66;
  font-size: 11px;
  cursor: pointer;
  padding: 2px 6px;
  line-height: 1;
}
.pw-toggle:hover {
  color: #8A8F98;
}
.login-btn {
  width: 100%;
  background: #E8E8ED;
  color: #09090B;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  font-size: 14px;
  height: 40px;
  cursor: pointer;
  box-sizing: border-box;
}
.login-btn:hover {
  background: #E8E8ED;
  opacity: 1;
}
.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.login-error {
  background: rgba(248,113,113,0.1);
  border: 1px solid rgba(248,113,113,0.3);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 12px;
  color: #f87171;
}
.mb-4 { margin-bottom: 16px; }
.mb-5 { margin-bottom: 20px; }
</style>
