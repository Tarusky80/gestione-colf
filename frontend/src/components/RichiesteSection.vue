<template>
  <div class="card-outlined">
    <div class="card-header">
      <span class="card-title">Richieste</span>
      <span v-if="richieste.length" class="card-count">{{ richieste.length }}</span>
    </div>
    <div class="card-body">
      <div v-if="richieste.length" class="item-list">
        <div v-for="r in richieste" :key="r.pk" class="item-row" :class="'border-' + r.stato.toLowerCase()" @click="$emit('vedi-dettaglio', r)">
          <div class="item-main">
            <span class="item-title">{{ r.tipo_display }}{{ r.etichetta_campo ? ' — ' + r.etichetta_campo : '' }}</span>
          </div>
          <div class="item-sub">
            {{ formatDate(r.creato_il) }}
          </div>
          <span v-if="r.nota_admin" class="item-reply">Risposta</span>
          <span class="chevron">▸</span>
        </div>
      </div>
      <div v-else class="empty">Nessuna richiesta inviata.</div>
    </div>
  </div>
</template>

<script setup>
defineProps({ richieste: { type: Array, default: () => [] } })
defineEmits(['vedi-dettaglio'])

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
.item-list { display: flex; flex-direction: column; }
.item-row {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  border-bottom: 1px solid #1E1E20; cursor: pointer;
  border-left: 3px solid transparent;
}
.item-row:last-child { border-bottom: none; }
.item-row:hover { opacity: 0.8; }
.border-inviata { border-left-color: #f59e0b; }
.border-vista { border-left-color: #38bdf8; }
.border-accettata { border-left-color: #34d399; }
.border-rifiutata { border-left-color: #f87171; }
.item-main { flex: 1; min-width: 0; }
.item-title { font-size: 13px; color: #E8E8ED; }
.item-sub { font-size: 11px; color: #5C5F66; }
.item-reply { font-size: 10px; color: #5E6AD2; }
.chevron { color: #5C5F66; font-size: 12px; }
.empty { text-align: center; padding: 20px 0; font-size: 12px; color: #5C5F66; }
</style>
