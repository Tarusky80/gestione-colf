import { defineStore } from 'pinia'
import client from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null,
    nome: localStorage.getItem('datore_nome') || '',
    codiceFiscale: localStorage.getItem('datore_cf') || '',
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    async login(codiceFiscale, password) {
      const { data } = await client.post('/token/', { codice_fiscale: codiceFiscale, password })
      this.token = data.access
      this.refreshToken = data.refresh
      this.nome = data.nome
      this.codiceFiscale = data.codice_fiscale
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      localStorage.setItem('datore_nome', data.nome)
      localStorage.setItem('datore_cf', data.codice_fiscale)
      return data
    },
    logout() {
      this.token = null
      this.refreshToken = null
      this.nome = ''
      this.codiceFiscale = ''
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('datore_nome')
      localStorage.removeItem('datore_cf')
    },
  },
})
