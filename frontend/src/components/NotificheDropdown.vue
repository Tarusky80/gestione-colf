<template>
  <div class="nd-wrap" ref="wrapRef">
    <button class="nd-trigger" @click="aperto = !aperto" :aria-label="'Notifiche: ' + conteggio + ' non lette'">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
      <span v-if="conteggio > 0" class="nd-badge">{{ conteggio > 99 ? '99+' : conteggio }}</span>
    </button>
    <transition name="nd-fade">
      <div v-if="aperto" class="nd-dropdown" role="menu" aria-label="Notifiche">
        <div class="nd-header">Notifiche</div>
        <div v-if="!richiestePending.length && !documentiNuovi.length" class="nd-empty">Nessuna notifica</div>
        <div v-if="richiestePending.length" class="nd-group">
          <div class="nd-group-title">Richieste pendenti</div>
          <div v-for="r in richiestePending" :key="r.pk" class="nd-item" role="menuitem" tabindex="0" @click="$emit('vedi-richiesta', r); aperto = false">
            <span class="nd-dot" style="background:#f59e0b;"></span>
            <div class="nd-text"><span class="nd-title">{{ r.tipo_display }}</span><span class="nd-sub">{{ giorniFa(r.creato_il) }}</span></div>
          </div>
        </div>
        <div v-if="documentiNuovi.length" class="nd-group">
          <div class="nd-group-title">Documenti recenti</div>
          <div v-for="d in documentiNuovi" :key="d.pk" class="nd-item" role="menuitem" tabindex="0" @click="scaricaDoc(d); aperto = false">
            <span class="nd-dot" style="background:#5E6AD2;"></span>
            <div class="nd-text"><span class="nd-title">{{ d.tipo_display || d.titolo }}</span><span class="nd-sub">{{ d.lavoratore_nome }}</span></div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({ richieste: { type: Array, default: () => [] }, documenti: { type: Array, default: () => [] } })
defineEmits(['vedi-richiesta'])

const aperto = ref(false)
const wrapRef = ref(null)

const richiestePending = computed(() => props.richieste.filter(r => r.stato === 'INVIATA').slice(0, 5))
const documentiNuovi = computed(() => props.documenti.filter(d => d.is_nuovo).slice(0, 5))
const conteggio = computed(() => richiestePending.value.length + documentiNuovi.value.length)

function giorniFa(iso) {
  if (!iso) return ''
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000)
  if (diff === 0) return 'Oggi'
  if (diff === 1) return 'Ieri'
  return diff + 'g fa'
}

function scaricaDoc(d) {
  const token = localStorage.getItem('access_token')
  window.open('/api/v1/documenti/' + d.pk + '/download/?token=' + token, '_blank')
}

function chiudiFuori(e) {
  if (wrapRef.value && !wrapRef.value.contains(e.target)) aperto.value = false
}
onMounted(() => document.addEventListener('click', chiudiFuori))
onUnmounted(() => document.removeEventListener('click', chiudiFuori))
</script>

<style scoped>
.nd-wrap { position: relative; }
.nd-trigger {
  position: relative; background: none; border: none; color: #5C5F66;
  cursor: pointer; display: flex; padding: 4px; border-radius: 4px;
}
.nd-trigger:hover { color: #8A8F98; background: rgba(255,255,255,0.04); }
.nd-badge {
  position: absolute; top: -2px; right: -2px;
  background: #f59e0b; color: #09090B; font-size: 9px; font-weight: 700;
  min-width: 14px; height: 14px; display: flex; align-items: center;
  justify-content: center; border-radius: 7px; padding: 0 3px;
}
.nd-dropdown {
  position: absolute; top: 100%; right: 0; margin-top: 6px;
  min-width: 260px; max-width: 320px;
  background: #131316; border: 1px solid #1E1E20; border-radius: 8px;
  z-index: 100; box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}
.nd-header { font-size: 12px; font-weight: 500; color: #E8E8ED; padding: 10px 14px; border-bottom: 1px solid #1E1E20; }
.nd-empty { padding: 20px; text-align: center; font-size: 12px; color: #5C5F66; }
.nd-group { border-top: 1px solid #1E1E20; }
.nd-group:first-of-type { border-top: none; }
.nd-group-title { font-size: 10px; color: #5C5F66; padding: 8px 14px 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.nd-item {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 8px 14px; cursor: pointer; transition: background 0.1s;
}
.nd-item:hover { background: rgba(255,255,255,0.03); }
.nd-dot { width: 6px; height: 6px; border-radius: 50%; margin-top: 4px; flex-shrink: 0; }
.nd-text { flex: 1; min-width: 0; }
.nd-title { font-size: 12px; color: #E8E8ED; display: block; }
.nd-sub { font-size: 10px; color: #5C5F66; }
.nd-fade-enter-active, .nd-fade-leave-active { transition: opacity 0.15s, transform 0.15s; }
.nd-fade-enter-from, .nd-fade-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
