<template>
  <div class="card-outlined">
    <div class="card-header">
      <span class="card-title">Documenti</span>
      <span v-if="documentiFiltrati.length" class="card-count">{{ documentiFiltrati.length }}</span>
    </div>
    <div class="card-body">
      <div class="filters">
        <select v-model="filtroTipo" class="filter-select">
          <option value="">Tutti i tipi</option>
          <option v-for="t in tipiDisponibili" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>
      <div v-if="documentiFiltrati.length" class="item-list">
        <a v-for="doc in documentiFiltrati" :key="doc.pk" :href="'/api/v1/documenti/' + doc.pk + '/download/?token=' + token" target="_blank" class="item-row">
          <div class="item-main">
            <span class="item-title">{{ doc.tipo_display }}{{ doc.titolo ? ' — ' + doc.titolo : '' }}</span>
            <span v-if="doc.is_nuovo" class="badge-nuovo">NUOVO</span>
          </div>
          <div class="item-sub">
            {{ formatDate(doc.creato_il) }}{{ doc.lavoratore_nome ? ' · ' + doc.lavoratore_nome : '' }}
          </div>
          <span class="chevron">▸</span>
        </a>
      </div>
      <div v-else class="empty">Nessun documento disponibile.</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const token = computed(() => localStorage.getItem('access_token') || '')

const props = defineProps({
  documenti: { type: Array, default: () => [] },
  tipiDisponibili: { type: Array, default: () => [] },
})

const filtroTipo = ref('')

const documentiFiltrati = computed(() => {
  if (!filtroTipo.value) return props.documenti
  return props.documenti.filter(d => d.tipo === filtroTipo.value)
})

function formatDate(d) {
  if (!d) return ''
  const dt = new Date(d)
  return String(dt.getDate()).padStart(2, '0') + '-' + String(dt.getMonth() + 1).padStart(2, '0') + '-' + dt.getFullYear()
}
</script>

<style scoped>
.card-outlined { border: 1px solid #1E1E20; border-radius: 8px; background: transparent; }
.card-header {
  display: flex; align-items: center; gap: 6px;
  padding: 12px 16px; border-bottom: 1px solid #1E1E20;
}
.card-title { font-size: 13px; font-weight: 500; color: #E8E8ED; }
.card-count { font-size: 11px; color: #5C5F66; }
.card-body { padding: 12px 16px; }
.filters { display: flex; gap: 8px; margin-bottom: 10px; }
@media (max-width: 767px) {
  .filters { flex-direction: column; }
  .card-body { padding: 10px 12px; }
}
.filter-select {
  background: #131316; border: 1px solid #1E1E20; border-radius: 6px;
  color: #E8E8ED; font-size: 12px; padding: 6px 10px; outline: none;
  width: 100%;
}
.item-list { display: flex; flex-direction: column; }
.item-row {
  display: flex; align-items: center; gap: 8px; padding: 8px 0;
  border-bottom: 1px solid #1E1E20; text-decoration: none; cursor: pointer;
}
.item-row:last-child { border-bottom: none; }
.item-row:hover { opacity: 0.8; }
.item-main { flex: 1; min-width: 0; }
.item-title { font-size: 13px; color: #E8E8ED; }
.badge-nuovo {
  font-size: 10px; color: #22c55e; border: 1px solid #22c55e;
  border-radius: 3px; padding: 0 4px; margin-left: 4px;
}
.item-sub { font-size: 11px; color: #5C5F66; }
.chevron { color: #5C5F66; font-size: 12px; }
.empty { text-align: center; padding: 20px 0; font-size: 12px; color: #5C5F66; }
</style>
