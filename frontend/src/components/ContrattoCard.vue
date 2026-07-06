<template>
  <div class="card-outlined mb-3">
    <div v-for="(c, i) in contratti" :key="c.id">
      <div class="contratto-row" :class="{ expanded: aperto === i, active: c.stato === 'ATTIVO' }" @click="toggle(i)">
        <span class="dot" :class="c.stato === 'ATTIVO' ? 'dot-green' : 'dot-grey'"></span>
        <span class="contratto-nome">{{ c.lavoratore_nome }}</span>
        <span v-if="c.stato_display" class="chip-min">{{ c.stato_display }}</span>
        <span v-if="c.is_convivente" class="chip-min">Conv.</span>
        <span v-else class="chip-min">Non conv.</span>
        <span v-if="c.tipo_contratto_display" class="chip-min">{{ c.tipo_contratto_display }}</span>
        <span class="spacer"></span>
        <span class="chevron">{{ aperto === i ? '▾' : '▸' }}</span>
      </div>
      <transition name="slide">
        <div v-if="aperto === i" class="contratto-details">
          <div class="details-grid">
            <div><span class="det-label">CF Lavoratore</span><span class="det-val">{{ c.lavoratore_cf }}</span></div>
            <div><span class="det-label">Data assunzione</span><span class="det-val">{{ formatDate(c.data_assunzione) }}</span></div>
            <div><span class="det-label">Data fine</span><span class="det-val">{{ formatDate(c.data_fine) }}</span></div>
            <div><span class="det-label">Codice INPS</span><span class="det-val">{{ c.codice_rapporto_inps || '-' }}</span></div>
            <div><span class="det-label">Budget mensile</span><span class="det-val">{{ formatEuro(c.budget_di_partenza) }}</span></div>
            <div><span class="det-label">Ore/mese</span><span class="det-val">{{ c.ore_calcolate ? c.ore_calcolate + 'h' : '-' }}</span></div>
            <div><span class="det-label">Ore settimanali</span><span class="det-val">{{ c.ore_settimanali_arrotondate }}h</span></div>
            <div><span class="det-label">Paga oraria</span><span class="det-val">{{ c.paga_applicata ? formatEuro(c.paga_applicata) + '/h' : '-' }}</span></div>
            <div><span class="det-label">Livello</span><span class="det-val">{{ c.livello_info?.codice || '' }}{{ c.livello_info?.descrizione ? ' — ' + c.livello_info.descrizione : '' }}</span></div>
            <div><span class="det-label">Ente bilaterale</span><span class="det-val">{{ c.ente_bilaterale_info?.descrizione || '-' }}</span></div>
            <div><span class="det-label">TFR</span><span class="det-val">{{ c.modalita_tfr_display }}</span></div>
            <div><span class="det-label">Convivente</span><span class="det-val">{{ c.is_convivente ? 'Sì' : 'No' }}</span></div>
            <div><span class="det-label">Scatti anzianità</span><span class="det-val">{{ c.applica_scatti ? 'Sì' : 'No' }}</span></div>
            <div><span class="det-label">Data inizio TFR</span><span class="det-val">{{ formatDate(c.data_inizio_tfr) }}</span></div>
          </div>
          <div class="detail-chips">
            <span v-if="c.paga_13ma" class="chip-flat">13ma</span>
            <span v-if="c.paga_ferie" class="chip-flat">Ferie</span>
            <span v-if="c.paga_festivi" class="chip-flat">Festivi</span>
          </div>
          <div class="detail-row" v-if="c.stima_trimestrale">
            <span class="det-label">Stima trim. contributi</span>
            <span class="det-val" style="color:#5E6AD2;">{{ formatEuro(c.stima_trimestrale) }}</span>
          </div>
          <div v-if="c.progetti?.length" class="detail-progetti">
            <div class="det-label mb-1">Progetti</div>
            <div v-for="p in c.progetti" :key="p.id" class="chip-flat">{{ p.beneficiario_nome }} — {{ p.tipo_nome }} ({{ formatEuro(p.budget_mensile) }})</div>
          </div>
          <div class="detail-buste">
            <div class="det-label mb-1">Buste paga</div>
            <div v-if="c.buste_paga?.length">
              <a v-for="b in c.buste_paga" :key="b.id" :href="'/api/v1/buste-paga/' + b.id + '/download/?token=' + token" target="_blank" class="busta-link">
                Busta Paga {{ b.mese }}/{{ b.anno }}
                <span class="busta-info">— {{ formatEuro(b.netto) }} netti · {{ b.tipo_calcolo }} · {{ b.ore_mensili }}h</span>
              </a>
            </div>
            <div v-else class="det-val">Nessuna busta paga disponibile.</div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

defineProps({ contratti: { type: Array, default: () => [] } })
const aperto = ref(null)
const token = computed(() => localStorage.getItem('access_token') || '')

function toggle(i) { aperto.value = aperto.value === i ? null : i }

function formatDate(val) {
  if (!val) return '-'
  if (val.includes('-')) { const p = val.split('-'); return p[2] + '-' + p[1] + '-' + p[0] }
  return val
}
function formatEuro(val) {
  if (val == null) return '-'
  return '€ ' + Number(val).toLocaleString('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 4 })
}
</script>

<style scoped>
.card-outlined {
  border: 1px solid #1E1E20;
  border-radius: 8px;
  background: transparent;
  overflow: hidden;
}
.contratto-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  border-bottom: 1px solid #1E1E20;
  transition: background 0.15s;
}
.contratto-row:hover { background: #131316; }
.contratto-row.expanded { background: #131316; }
.contratto-row.active {
  position: relative;
}
.contratto-row.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(to bottom, #22c55e, #5E6AD2);
  pointer-events: none;
}
.contratto-row:last-child { border-bottom: none; }
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-green { background: #22c55e; }
.dot-grey { background: #5C5F66; }
.contratto-nome {
  font-size: 13px;
  color: #E8E8ED;
  font-weight: 500;
}
.chip-min {
  font-size: 10px;
  color: #8A8F98;
  border: 1px solid #1E1E20;
  border-radius: 4px;
  padding: 2px 6px;
  line-height: 14px;
  white-space: nowrap;
}
.spacer { flex: 1; }
.chevron {
  color: #5C5F66;
  font-size: 12px;
}
.contratto-details {
  padding: 16px;
  border-bottom: 1px solid #1E1E20;
  background: #0D0D10;
}
.contratto-details:last-child { border-bottom: none; }
.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 12px;
}
@media (max-width: 767px) {
  .details-grid { grid-template-columns: 1fr; }
  .contratto-row { flex-wrap: wrap; gap: 4px; padding: 8px 12px; }
  .contratto-nome { width: 100%; }
  .contratto-details { padding: 12px; }
}
.det-label {
  font-size: 11px;
  color: #8A8F98;
  display: block;
  margin-bottom: 1px;
}
.det-val {
  font-size: 13px;
  color: #E8E8ED;
}
.detail-chips {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
}
.chip-flat {
  font-size: 11px;
  color: #8A8F98;
  border: 1px solid #1E1E20;
  border-radius: 4px;
  padding: 2px 8px;
  display: inline-block;
}
.detail-row {
  margin-bottom: 10px;
}
.detail-progetti {
  margin-bottom: 12px;
}
.detail-buste {
  margin-top: 8px;
}
.busta-link {
  display: block;
  font-size: 13px;
  color: #5E6AD2;
  text-decoration: none;
  padding: 4px 0;
}
.busta-link:hover { text-decoration: underline; }
.busta-info {
  font-size: 11px;
  color: #5C5F66;
}
.slide-enter-active { transition: all 0.2s ease; }
.slide-leave-active { transition: all 0.15s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; max-height: 0; padding: 0 16px; }
.slide-enter-to, .slide-leave-from { opacity: 1; }
</style>
