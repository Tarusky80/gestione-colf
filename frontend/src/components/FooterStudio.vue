<template>
  <div class="foot-wrap">
    <div class="foot-line">
      <span class="foot-t">{{ nomeProgramma || 'Gestionale COLF' }}</span>
      <span class="foot-d">·</span>
      <span class="foot-t">v{{ versione || '1.1' }}</span>
    </div>
    <div v-if="denominazione" class="foot-line">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#5C5F66" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      <span class="foot-t">CREATO DA: {{ denominazione }}</span>
    </div>
    <div v-if="datiStudio" class="foot-line">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#5C5F66" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
      <span class="foot-t">{{ datiStudio }}</span>
    </div>
    <div class="foot-line">
      <svg v-if="telefono" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#5C5F66" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
      <span v-if="telefono" class="foot-t">{{ telefono }}</span>
      <svg v-if="email" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#5C5F66" stroke-width="1.5" stroke-linecap="round" aria-hidden="true" class="foot-ico-spacer"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
      <a v-if="email" :href="'mailto:' + email" class="foot-link">{{ email }}</a>
    </div>
    <div class="foot-line">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#5C5F66" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      <span class="foot-t">AGGIORNATO A: {{ dataOdierna }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

defineProps({
  logoUrl: { type: String, default: '' },
  datiStudio: { type: String, default: '' },
  telefono: { type: String, default: '' },
  email: { type: String, default: '' },
  nomeProgramma: { type: String, default: '' },
  versione: { type: String, default: '' },
  denominazione: { type: String, default: '' },
})

const dataOdierna = computed(() => {
  return new Date().toLocaleDateString('it-IT', { day: '2-digit', month: 'long', year: 'numeric' })
})
</script>

<style scoped>
.foot-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 14px 16px;
  border-top: 1px solid #1E1E20;
  margin-top: 8px;
}
.foot-line {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
  justify-content: center;
}
.foot-t {
  font-size: 10px;
  color: #3A3B40;
}
.foot-d {
  font-size: 10px;
  color: #3A3B40;
}
.foot-link {
  font-size: 10px;
  color: #5E6AD2;
  text-decoration: none;
}
.foot-link:hover {
  text-decoration: underline;
  color: #7c85e0;
}
.foot-ico-spacer {
  margin-left: 4px;
}
</style>
