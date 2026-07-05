<template>
  <div class="sc-card" role="region" aria-label="Scadenze">
    <div class="sc-heading">Scadenze</div>
    <div v-if="!scadenze.length" class="sc-empty">Nessuna scadenza imminente</div>
    <div v-for="(s, i) in scadenze" :key="i" class="sc-row" :class="{ 'sc-overdue': s.giorni <= 0 }">
      <span class="sc-dot" :style="{ background: coloreTipo(s.tipo) }"></span>
      <span class="sc-label">{{ s.label }}</span>
      <span class="spacer"></span>
      <span class="sc-data">{{ s.data }}</span>
      <span class="sc-count" :class="{ 'sc-count-warn': s.giorni > 0 && s.giorni <= 7 }">{{ s.giorni > 0 ? s.giorni + 'g' : 'Scaduta' }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({ scadenze: { type: Array, default: () => [] } })
function coloreTipo(t) { return { contributo: '#5E6AD2', f24: '#f59e0b', contratto: '#34d399' }[t] || '#5C5F66' }
</script>

<style scoped>
.sc-card {
  border: 1px solid #1E1E20; border-radius: 8px; padding: 14px;
  background: transparent;
}
.sc-heading { font-size: 12px; font-weight: 500; color: #E8E8ED; margin-bottom: 10px; }
.sc-empty { font-size: 11px; color: #5C5F66; }
.sc-row {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 0; border-bottom: 1px solid #1E1E20; font-size: 12px;
}
.sc-row:last-child { border-bottom: none; }
.sc-overdue { opacity: 0.6; }
.sc-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }
.sc-label { color: #E8E8ED; font-size: 11px; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sc-data { font-size: 11px; color: #5C5F66; flex-shrink: 0; }
.sc-count { font-size: 10px; color: #5C5F66; font-weight: 500; flex-shrink: 0; min-width: 34px; text-align: right; }
.sc-count-warn { color: #f59e0b; }
</style>
