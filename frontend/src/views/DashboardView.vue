<template>
  <div>
    <div class="header-bar">
      <span class="avatar-circle" :style="{ background: coloreAvatar }" aria-label="Profilo">{{ iniziali }}</span>
      <div class="header-nome-wrap">
        <span class="header-nome">{{ authStore.nome }}</span>
        <span class="header-cf">{{ authStore.codiceFiscale }}</span>
      </div>
      <span class="spacer"></span>
      <NotificheDropdown :richieste="richieste" :documenti="documenti" @vedi-richiesta="vediDettaglioRichiesta" />
      <button class="btn-esci" @click="logout" aria-label="Esci">Esci</button>
    </div>

    <div class="search-bar">
      <input v-model="ricerca" placeholder="Cerca contratti, documenti, richieste..." class="search-input" aria-label="Ricerca" />
    </div>

    <div class="content-area">
      <div v-if="erroreCaricamento" class="alert-error mb-4" role="alert">
        {{ erroreCaricamento }}
        <button class="alert-close" @click="erroreCaricamento = ''" aria-label="Chiudi">&times;</button>
      </div>

      <template v-if="caricamento">
        <div class="stat-row">
          <div v-for="n in 4" :key="n" class="stat-card-skeleton"></div>
        </div>
        <div class="skeleton-card mt-4"></div>
        <div class="skeleton-card mt-4"></div>
      </template>

      <transition name="fade" mode="out-in">
        <div v-if="!caricamento" key="content">
          <div class="stat-row">
            <div class="stat-card"><div class="stat-number">{{ animContratti }}</div><div class="stat-label">Contratti attivi</div></div>
            <div class="stat-card"><div class="stat-number">{{ animDocumenti }}</div><div class="stat-label">Documenti</div></div>
            <div class="stat-card"><div class="stat-number">{{ animRichieste }}</div><div class="stat-label">Richieste pendenti</div></div>
            <div class="stat-card"><div class="stat-number">{{ ultimoAccesso || '—' }}</div><div class="stat-label">Ultimo accesso</div></div>
          </div>

          <div class="mini-stato">
            <div class="mini-card">
              <span class="mini-num">{{ animContratti }}</span>
              <span class="mini-label">Contratti attivi</span>
            </div>
            <div class="mini-card">
              <span class="mini-num" :class="{ 'text-warn': contrattiInScadenza > 0 }">{{ contrattiInScadenza }}</span>
              <span class="mini-label">In scadenza &lt;30gg</span>
              <div class="mini-bar"><div class="mini-fill" :style="{ width: (contrattiFiltrati.length ? (contrattiFiltrati.filter(c => c.stato === 'ATTIVO').length ? (contrattiInScadenza / contrattiFiltrati.filter(c => c.stato === 'ATTIVO').length * 100) : 0) : 0) + '%' }"></div></div>
            </div>
            <div class="mini-card">
              <span class="mini-num">{{ animDocumenti }}</span>
              <span class="mini-label">Documenti</span>
            </div>
            <div class="mini-card">
              <span class="mini-num">{{ animRichieste }}</span>
              <span class="mini-label">Richieste pendenti</span>
            </div>
          </div>

          <div class="quick-actions">
            <button class="qa-btn" @click="apriModalRichiesta" aria-label="Nuova richiesta">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              Nuova richiesta
            </button>
            <button class="qa-btn" :disabled="!ultimaCU" @click="scaricaCU" aria-label="Scarica CU">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Scarica CU
            </button>
            <button class="qa-btn" :disabled="!contratti.length" @click="apriPagopa" aria-label="Prossimo PAGOPA">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              Prossimo PAGOPA
            </button>
            <button class="qa-btn" :disabled="!ultimaBusta" @click="scaricaUltimaBusta" aria-label="Ultima busta paga">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Ultima busta paga
            </button>
            <button class="qa-btn" :disabled="!studio?.iban_studio" @click="apriDatiBonifico" aria-label="Dati bonifico">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
              Dati bonifico
            </button>
          </div>

          <div class="scadenze-chart-row">
            <ScadenzeCard :scadenze="scadenze" />
            <IndicatoriDashboard :contratti="contrattiFiltrati" :scadenze="scadenze" />
          </div>

          <AnagraficaCard v-if="datore" :datore="datore" @apri-richiesta="apriModalRichiesta" />

          <div v-if="busteRecenti.length" class="card-outlined mb-3">
            <div class="card-header"><span class="card-title">Buste paga recenti</span><span class="card-count">{{ busteRecenti.length }}</span></div>
            <div class="card-body">
              <div v-for="b in busteRecenti" :key="b.id" class="busta-row" @click="scaricaBusta(b)">
                <span class="busta-mese">{{ b.mese }}/{{ b.anno }}</span>
                <span class="busta-lavoratore">{{ b.lavoratore_nome }}</span>
                <span class="spacer"></span>
                <span class="busta-importo">{{ formatEuro(b.netto) }}</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:#5C5F66;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              </div>
            </div>
          </div>

          <div class="doc-buttons">
            <button class="doc-btn" @click="apriDoc('ccnl')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
              CCNL
            </button>
            <button class="doc-btn" @click="apriDoc('inquadramento')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
              Inquadramento
            </button>
            <button class="doc-btn" @click="apriDoc('tabelle')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
              Tabelle Retributive
            </button>
            <button class="doc-btn" @click="apriDoc('contributi')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
              Contributi INPS
            </button>
            <button class="doc-btn" @click="apriDoc('assunzione')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M9 15l2 2 4-4"/></svg>
              Guida Assunzione
            </button>
            <button class="doc-btn" @click="apriDoc('decalogo')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
              Decalogo Colloquio
            </button>
            <button class="doc-btn" @click="apriDoc('cessazione')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
              Guida Cessazione
            </button>
          </div>

          <div class="section-header">
            <span class="section-title">Contratti</span>
            <span v-if="contrattiFiltrati.length" class="section-count">{{ contrattiFiltrati.length }}</span>
          </div>
          <ContrattoCard :contratti="contrattiFiltrati" />

          <div class="two-col">
            <DocumentiSection :documenti="documentiFiltrati" :tipiDisponibili="tipiDocumenti" />
            <RichiesteSection :richieste="richiesteFiltrate" @vedi-dettaglio="vediDettaglioRichiesta" />
          </div>
        </div>
      </transition>
    </div>

    <FooterStudio
      :logoUrl="studio?.logo_url"
      :datiStudio="studio?.dati_studio"
      :telefono="studio?.telefono_studio"
      :email="studio?.email_studio"
      :nomeProgramma="studio?.nome_programma"
      :versione="studio?.versione_programma"
      :denominazione="studio?.denominazione_studio"
    />

    <NuovaRichiestaModal v-model="modalRichiestaAperta" @inviata="ricaricaRichieste" />

    <TeleportModal v-model="modalDettaglioAperta">
      <div v-if="richiestaCorrente" class="detail-card">
        <div class="detail-title">Dettaglio Richiesta</div>
        <div class="detail-body">
          <div class="detail-field"><div class="detail-label">Tipo</div><div class="detail-value">{{ richiestaCorrente.tipo_display }}</div></div>
          <div v-if="richiestaCorrente.etichetta_campo" class="detail-field"><div class="detail-label">Campo</div><div class="detail-value">{{ richiestaCorrente.etichetta_campo }}</div></div>
          <div class="detail-field">
            <div class="detail-label">Stato</div>
            <span class="detail-chip" :style="{ background: coloreStatoBg(richiestaCorrente.stato) }">{{ richiestaCorrente.stato_display }}</span>
          </div>
          <div v-if="richiestaCorrente.valore_attuale" class="detail-field"><div class="detail-label">Valore attuale</div><div class="detail-value" style="color:#f87171;">{{ richiestaCorrente.valore_attuale }}</div></div>
          <div v-if="richiestaCorrente.valore_richiesto" class="detail-field"><div class="detail-label">Valore richiesto</div><div class="detail-value" style="color:#34d399;">{{ richiestaCorrente.valore_richiesto }}</div></div>
          <div v-if="richiestaCorrente.nota_datore" class="detail-field"><div class="detail-label">Nota</div><div class="detail-value" style="color:#f59e0b;">{{ richiestaCorrente.nota_datore }}</div></div>
          <div v-if="richiestaCorrente.nota_admin" class="detail-field"><div class="detail-label">Risposta admin</div><div class="detail-value" style="color:#38bdf8;">{{ richiestaCorrente.nota_admin }}</div></div>
        </div>
        <div class="detail-actions"><button class="detail-btn-close" @click="modalDettaglioAperta = false">Chiudi</button></div>
      </div>
    </TeleportModal>

    <TeleportModal v-model="modalBonificoAperta">
      <div class="detail-card">
        <div class="detail-title">Dati bonifico</div>
        <div class="detail-body">
          <div class="detail-field"><div class="detail-label">Intestatario</div><div class="detail-value">{{ studio?.intestatario_iban || '—' }}</div></div>
          <div class="detail-field"><div class="detail-label">Banca</div><div class="detail-value">{{ studio?.banca_iban || '—' }}</div></div>
          <div class="detail-field">
            <div class="detail-label">IBAN</div>
            <div class="iban-row">
              <span class="detail-value iban-text">{{ studio?.iban_studio || 'Non disponibile' }}</span>
              <button class="copy-btn" @click="copiaIBAN" title="Copia IBAN">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              </button>
            </div>
          </div>
        </div>
        <div class="detail-actions"><button class="detail-btn-close" @click="modalBonificoAperta = false">Chiudi</button></div>
      </div>
    </TeleportModal>

    <Toast v-model:visibile="snackbar.visibile" :messaggio="snackbar.messaggio" :colore="snackbar.colore" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import client from '../api/client'
import AnagraficaCard from '../components/AnagraficaCard.vue'
import ContrattoCard from '../components/ContrattoCard.vue'
import DocumentiSection from '../components/DocumentiSection.vue'
import RichiesteSection from '../components/RichiesteSection.vue'
import NuovaRichiestaModal from '../components/NuovaRichiestaModal.vue'
import FooterStudio from '../components/FooterStudio.vue'
import AppIcon from '../components/AppIcon.vue'
import NotificheDropdown from '../components/NotificheDropdown.vue'
import ScadenzeCard from '../components/ScadenzeCard.vue'
import IndicatoriDashboard from '../components/IndicatoriDashboard.vue'
import TeleportModal from '../components/TeleportModal.vue'
import Toast from '../components/Toast.vue'

const router = useRouter()
const authStore = useAuthStore()

const caricamento = ref(true)
const erroreCaricamento = ref('')
const datore = ref(null)
const contratti = ref([])
const documenti = ref([])
const tipiDocumenti = ref([])
const richieste = ref([])
const studio = ref(null)
const snackbar = ref({ visibile: false, messaggio: '', colore: 'success' })
const modalRichiestaAperta = ref(false)
const modalDettaglioAperta = ref(false)
const modalBonificoAperta = ref(false)
const richiestaCorrente = ref(null)
const ricerca = ref('')

const richiestePendenti = computed(() => richieste.value.filter(r => r.stato === 'INVIATA').length)

const iniziali = computed(() => {
  const n = authStore.nome || ''
  const p = n.split(' ')
  return (p[0]?.[0] || '') + (p[1]?.[0] || '')
})

const coloreAvatar = computed(() => {
  const n = authStore.nome || ''
  let h = 0; for (let i = 0; i < n.length; i++) h = (h * 31 + n.charCodeAt(i)) % 360
  return `hsl(${h}, 55%, 45%)`
})

function tempoRelativo(iso) {
  if (!iso) return '—'
  const d = new Date(iso), ora = new Date()
  const diff = Math.floor((ora - d) / 1000)
  if (diff < 60) return 'Ora'
  if (diff < 3600) return Math.floor(diff / 60) + 'm fa'
  if (diff < 86400) return Math.floor(diff / 3600) + 'h fa'
  const gg = Math.floor(diff / 86400)
  if (gg < 30) return gg + 'g fa'
  if (gg < 365) return Math.floor(gg / 30) + ' mesi fa'
  return Math.floor(gg / 365) + ' anni fa'
}

const ultimoAccesso = computed(() => {
  if (!datore.value?.ultimo_accesso) return '—'
  return tempoRelativo(datore.value.ultimo_accesso)
})

function logout() { authStore.logout(); router.push('/login') }
function apriModalRichiesta() { modalRichiestaAperta.value = true }

function vediDettaglioRichiesta(r) {
  richiestaCorrente.value = r
  modalDettaglioAperta.value = true
}

function coloreStatoBg(stato) {
  return { INVIATA: 'rgba(245,158,11,0.15)', VISTA: 'rgba(56,189,248,0.15)', ACCETTATA: 'rgba(52,211,153,0.15)', RIFIUTATA: 'rgba(248,113,113,0.15)' }[stato] || 'rgba(90,90,100,0.15)'
}

function formatEuro(val) {
  if (val == null) return '-'
  return '€ ' + Number(val).toLocaleString('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const t = new RegExp('', 'i')
const contrattiFiltrati = computed(() => {
  if (!ricerca.value) return contratti.value
  const q = ricerca.value.toLowerCase()
  return contratti.value.filter(c =>
    c.lavoratore_nome?.toLowerCase().includes(q) ||
    c.lavoratore_cf?.toLowerCase().includes(q)
  )
})

const documentiFiltrati = computed(() => {
  if (!ricerca.value) return documenti.value
  const q = ricerca.value.toLowerCase()
  return documenti.value.filter(d =>
    d.lavoratore_nome?.toLowerCase().includes(q) ||
    d.tipo_display?.toLowerCase().includes(q)
  )
})

const richiesteFiltrate = computed(() => {
  if (!ricerca.value) return richieste.value
  const q = ricerca.value.toLowerCase()
  return richieste.value.filter(r =>
    r.tipo_display?.toLowerCase().includes(q) ||
    r.etichetta_campo?.toLowerCase().includes(q)
  )
})

const contrattiInScadenza = computed(() => {
  const oggi = new Date()
  const tra30 = new Date(oggi.getTime() + 30 * 86400000)
  return contratti.value.filter(c => {
    if (!c.data_fine || c.stato !== 'ATTIVO') return false
    const fine = new Date(c.data_fine.split('-')[0], c.data_fine.split('-')[1] - 1, c.data_fine.split('-')[2])
    return fine >= oggi && fine <= tra30
  }).length
})

const busteRecenti = computed(() => {
  const tutte = contratti.value.flatMap(c => c.buste_paga || [])
  tutte.sort((a, b) => b.anno - a.anno || b.mese - a.mese)
  return tutte.slice(0, 3)
})

const ultimaBusta = computed(() => {
  const tutte = contratti.value.flatMap(c => c.buste_paga || [])
  tutte.sort((a, b) => b.anno - a.anno || b.mese - a.mese)
  return tutte[0] || null
})

const ultimaCU = computed(() => {
  return documenti.value.find(d => d.tipo === 'CU' || d.tipo_display?.includes('Certificazione'))
})

const scadenze = computed(() => {
  const oggi = new Date()
  const anno = oggi.getFullYear()
  const elenco = []

  const trimestri = [[1, 10], [4, 10], [7, 10], [10, 10]]
  const etichetteTrim = ['GEN', 'APR', 'LUG', 'OTT']
  for (let i = 0; i < trimestri.length; i++) {
    const [m, g] = trimestri[i]
    let d = new Date(anno, m - 1, g)
    if (d <= oggi) d = new Date(anno + 1, m - 1, g)
    elenco.push({ label: 'Contributi ' + etichetteTrim[i], data: d.toLocaleDateString('it-IT'), giorni: Math.ceil((d - oggi) / 86400000), tipo: 'contributo' })
  }

  const f24Nov = new Date(anno, 10, 30)
  if (f24Nov > oggi) elenco.push({ label: '2° rata F24', data: f24Nov.toLocaleDateString('it-IT'), giorni: Math.ceil((f24Nov - oggi) / 86400000), tipo: 'f24' })

  for (const c of contratti.value) {
    if (c.data_fine) {
      const fine = new Date(c.data_fine.split('-')[0], c.data_fine.split('-')[1] - 1, c.data_fine.split('-')[2])
      if (fine > oggi) elenco.push({ label: 'Fine contratto ' + c.lavoratore_nome, data: fine.toLocaleDateString('it-IT'), giorni: Math.ceil((fine - oggi) / 86400000), tipo: 'contratto' })
    }
  }

  if (!elenco.length) return []
  elenco.sort((a, b) => a.giorni - b.giorni)
  return elenco.slice(0, 6)
})

// --- count-up animation ---
const animContratti = ref(0)
const animDocumenti = ref(0)
const animRichieste = ref(0)

function countUp(refVal, target, duration = 400) {
  if (target < 0) target = 0
  const start = refVal.value
  const diff = target - start
  if (diff === 0) return
  const t0 = performance.now()
  function tick(now) {
    const p = Math.min((now - t0) / duration, 1)
    refVal.value = Math.round(start + diff * p)
    if (p < 1) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}

watch(() => contrattiFiltrati.value.length, (v) => countUp(animContratti, v))
watch(() => documentiFiltrati.value.length, (v) => countUp(animDocumenti, v))
watch(() => richiestePendenti.value, (v) => countUp(animRichieste, v), { immediate: true })

function scaricaCU() {
  if (!ultimaCU.value) return
  const token = localStorage.getItem('access_token')
  window.open('/api/v1/documenti/' + ultimaCU.value.pk + '/download/?token=' + token, '_blank')
}

function apriPagopa() {
  if (!contratti.value.length) return
  const oggi = new Date()
  const anno = oggi.getFullYear()
  const trimDate = [
    { m: 0, g: 10, trim: '4° trimestre anno prec.', label: 'Contributi 4° trimestre' },
    { m: 3, g: 10, trim: '1° trimestre', label: 'Contributi 1° trimestre' },
    { m: 6, g: 10, trim: '2° trimestre', label: 'Contributi 2° trimestre' },
    { m: 9, g: 10, trim: '3° trimestre', label: 'Contributi 3° trimestre' },
  ]
  let prox = null
  for (const t of trimDate) {
    const d = new Date(anno, t.m, t.g)
    if (d >= oggi) { prox = { ...t, data: d }; break }
  }
  if (!prox) {
    const t = trimDate[0]
    prox = { ...t, data: new Date(anno + 1, t.m, t.g) }
  }
  const diff = Math.ceil((prox.data - oggi) / (1000 * 60 * 60 * 24))
  const dd = String(prox.data.getDate()).padStart(2, '0')
  const mm = String(prox.data.getMonth() + 1).padStart(2, '0')
  const yyyy = prox.data.getFullYear()
  snackbar.value = { visibile: true, messaggio: `${prox.label} — ${dd}/${mm}/${yyyy} (${diff}g)`, colore: 'info' }
}

function scaricaUltimaBusta() {
  if (!ultimaBusta.value) return
  scaricaBusta(ultimaBusta.value)
}

function apriDatiBonifico() {
  modalBonificoAperta.value = true
}

function copiaIBAN() {
  const iban = studio.value?.iban_studio
  if (!iban) return
  navigator.clipboard.writeText(iban).then(() => {
    snackbar.value = { visibile: true, messaggio: 'IBAN copiato negli appunti', colore: 'success' }
  }).catch(() => {
    snackbar.value = { visibile: true, messaggio: 'Errore copia IBAN', colore: 'error' }
  })
}

function apriDoc(tipo) {
  const token = localStorage.getItem('access_token')
  const m = { ccnl: 'ccnl', inquadramento: 'inquadramento', tabelle: 'tabelle', contributi: 'contributi', assunzione: 'assunzione', decalogo: 'decalogo', cessazione: 'cessazione' }
  window.open('/api/v1/referenza-pdf/' + (m[tipo] || '') + '/?token=' + token, '_blank')
}

function scaricaBusta(b) {
  const token = localStorage.getItem('access_token')
  window.open('/api/v1/buste-paga/' + b.id + '/download/?token=' + token, '_blank')
}

async function ricaricaRichieste() {
  try { const { data } = await client.get('/richieste/'); richieste.value = data } catch { }
}

async function caricaDati() {
  caricamento.value = true
  erroreCaricamento.value = ''
  try {
    const [profilo, contrattiRes, documentiRes, richiesteRes, studioRes] = await Promise.all([
      client.get('/datore/profilo/'),
      client.get('/contratti/'),
      client.get('/documenti/'),
      client.get('/richieste/'),
      client.get('/studio/'),
    ])
    datore.value = profilo.data
    contratti.value = contrattiRes.data
    documenti.value = documentiRes.data.documenti
    tipiDocumenti.value = documentiRes.data.tipi_disponibili || []
    richieste.value = richiesteRes.data
    studio.value = studioRes.data
  } catch (err) {
    erroreCaricamento.value = 'Errore nel caricamento dei dati.'
    if (err.response?.status === 401) { authStore.logout(); window.location.href = '/portal/login' }
  } finally { caricamento.value = false }
}

onMounted(caricaDati)
</script>

<style scoped>
.header-bar {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  border-bottom: 1px solid #1E1E20;
  gap: 8px;
}
.header-nome { font-size: 14px; color: #E8E8ED; font-weight: 500; }
.header-cf { font-size: 12px; color: #5C5F66; }
.header-nome-wrap { display: flex; flex-direction: column; gap: 0; line-height: 1.3; }
.avatar-circle {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 13px; font-weight: 600; flex-shrink: 0;
  letter-spacing: 0.5px;
}
.spacer { flex: 1; }
.btn-esci {
  background: none; border: none; color: #5C5F66; font-size: 13px;
  cursor: pointer; padding: 4px 8px; border-radius: 4px;
}
.btn-esci:hover { background: rgba(248,113,113,0.15); }

.search-bar {
  padding: 12px 24px 0;
}
.search-input {
  width: 100%; height: 32px;
  background: #131316; border: 1px solid #1E1E20; border-radius: 6px;
  color: #E8E8ED; font-size: 12px; padding: 6px 12px; outline: none;
  box-sizing: border-box;
}
.search-input::placeholder { color: #5C5F66; }
.search-input:focus { border-color: #5E6AD2; }

.content-area { padding: 20px 24px; }
@media (max-width: 767px) {
  .content-area { padding: 12px 16px; }
  .header-bar { padding: 10px 16px; flex-wrap: wrap; }
  .header-cf { display: none; }
  .search-bar { padding: 10px 16px 0; }
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
@media (max-width: 767px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); gap: 8px; }
}
.stat-card {
  background: transparent;
  border: 1px solid #1E1E20;
  border-radius: 8px;
  padding: 16px;
}
@media (max-width: 767px) {
  .stat-card { padding: 12px; }
}
.stat-number {
  font-size: 32px;
  font-weight: 600;
  color: #E8E8ED;
  line-height: 1.1;
}
@media (max-width: 767px) {
  .stat-number { font-size: 24px; }
}
.stat-label { font-size: 11px; color: #8A8F98; margin-top: 4px; }
.stat-card-skeleton { background: #131316; border: 1px solid #1E1E20; border-radius: 8px; height: 72px; animation: pulse 1.5s infinite; }
.skeleton-card { background: #131316; border: 1px solid #1E1E20; border-radius: 8px; height: 120px; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.7; } }

.mini-stato {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}
@media (max-width: 767px) {
  .mini-stato { grid-template-columns: repeat(2, 1fr); gap: 6px; }
}
.mini-card {
  background: transparent;
  border: 1px solid #1E1E20;
  border-radius: 6px;
  padding: 10px 12px;
}
.mini-num { font-size: 18px; font-weight: 600; color: #E8E8ED; display: block; line-height: 1.2; }
.text-warn { color: #f59e0b; }
.mini-label { font-size: 10px; color: #8A8F98; margin-top: 2px; display: block; }
.mini-bar { margin-top: 6px; height: 3px; background: #1E1E20; border-radius: 2px; overflow: hidden; }
.mini-fill { height: 100%; background: #5E6AD2; border-radius: 2px; transition: width 0.5s ease; }

.quick-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.qa-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: 1px solid #1E1E20;
  border-radius: 6px;
  color: #8A8F98;
  font-size: 12px;
  padding: 8px 14px;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}
.qa-btn:hover { border-color: #5E6AD2; color: #E8E8ED; }
.qa-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.qa-btn:disabled:hover { border-color: #1E1E20; color: #8A8F98; }

.scadenze-chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}
@media (max-width: 767px) {
  .scadenze-chart-row { grid-template-columns: 1fr; }
}

.card-outlined { border: 1px solid #1E1E20; border-radius: 8px; background: transparent; overflow: hidden; }
.card-header {
  display: flex; align-items: center; gap: 6px;
  padding: 12px 16px; border-bottom: 1px solid #1E1E20;
}
.card-title { font-size: 13px; font-weight: 500; color: #E8E8ED; }
.card-count { font-size: 11px; color: #5C5F66; }
.card-body { padding: 12px 16px; }

.busta-row {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 0; border-bottom: 1px solid #1E1E20;
  cursor: pointer;
}
.busta-row:last-child { border-bottom: none; }
.busta-row:hover { opacity: 0.8; }
.busta-mese { font-size: 13px; color: #E8E8ED; font-weight: 500; }
.busta-lavoratore { font-size: 12px; color: #8A8F98; }
.busta-importo { font-size: 13px; color: #34d399; font-weight: 500; }

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  margin-top: 20px;
}
.section-title { font-size: 13px; font-weight: 500; color: #E8E8ED; }
.section-count { font-size: 11px; color: #5C5F66; }

.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 20px;
}
@media (max-width: 767px) {
  .two-col { grid-template-columns: 1fr; }
}

.doc-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}
.doc-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: 1px solid #1E1E20;
  border-radius: 8px;
  color: #8A8F98;
  font-size: 11px;
  padding: 10px 14px;
  cursor: pointer;
  transition: all 0.15s;
  flex: 0 1 auto;
}
.doc-btn:hover {
  border-color: rgba(94,106,210,0.4);
  color: #E8E8ED;
  background: rgba(94,106,210,0.06);
}
@media (max-width: 767px) {
  .doc-btn { flex: 1 1 calc(50% - 8px); justify-content: center; }
}

.iban-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.iban-text {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 15px;
  letter-spacing: 1px;
  color: #34d399;
  word-break: break-all;
}
.copy-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid #1E1E20;
  border-radius: 4px;
  color: #5C5F66;
  width: 28px;
  height: 28px;
  cursor: pointer;
  flex-shrink: 0;
  transition: border-color 0.15s, color 0.15s;
}
.copy-btn:hover { border-color: #34d399; color: #34d399; }

.alert-error {
  background: rgba(248,113,113,0.1);
  border: 1px solid rgba(248,113,113,0.3);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 12px;
  color: #f87171;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.alert-close { background: none; border: none; color: #f87171; font-size: 16px; cursor: pointer; padding: 0 4px; }

.detail-card { background: #09090B; border: 1px solid #1E1E20; border-radius: 8px; }
.detail-title { font-size: 14px; font-weight: 500; color: #E8E8ED; padding: 16px 20px 8px; }
.detail-body { padding: 8px 20px; }
.detail-field { margin-bottom: 12px; }
.detail-label { font-size: 11px; color: #8A8F98; margin-bottom: 2px; }
.detail-value { font-size: 13px; color: #E8E8ED; }
.detail-chip { display: inline-block; font-size: 11px; color: #E8E8ED; padding: 2px 8px; border-radius: 4px; }
.detail-actions { padding: 8px 20px 16px; display: flex; justify-content: flex-end; }
.detail-btn-close { background: none; border: none; color: #5C5F66; font-size: 12px; cursor: pointer; padding: 6px 12px; }
.detail-btn-close:hover { color: #8A8F98; }

.mb-3 { margin-bottom: 12px; }
.mb-4 { margin-bottom: 16px; }
.mt-4 { margin-top: 16px; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.25s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
