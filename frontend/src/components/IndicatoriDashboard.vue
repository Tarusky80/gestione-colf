<template>
  <div class="ic-card" role="region" aria-label="Altre statistiche">
    <div class="ic-heading">Altre statistiche</div>
    <div class="ic-wrap">
      <div class="ic-row">
        <div class="ic-lbl">
          <span class="ic-dot" style="background:#5E6AD2;"></span>
          <span>Contributi trimestre</span>
        </div>
        <div class="ic-bar-wrap">
          <div class="ic-bar" :style="{ width: contributiPct + '%', background: '#5E6AD2' }"></div>
        </div>
        <div class="ic-val">{{ formatEuro(contributiTot) }}</div>
      </div>

      <div class="ic-row">
        <div class="ic-lbl">
          <span class="ic-dot" :style="{ background: scadenzaColore }"></span>
          <span>{{ scadenzaLabel }}</span>
        </div>
        <div class="ic-bar-wrap">
          <div class="ic-bar" :style="{ width: scadenzaPct + '%', background: scadenzaColore }"></div>
        </div>
        <div class="ic-val">{{ scadenzaGiorni > 0 ? scadenzaGiorni + 'g' : 'Scaduta' }}</div>
      </div>

      <div class="ic-row">
        <div class="ic-lbl">
          <span class="ic-dot" style="background:#5E6AD2;"></span>
          <span>Fine mese</span>
        </div>
        <div class="ic-bar-wrap">
          <div class="ic-bar" :style="{ width: mesePct + '%', background: '#5E6AD2' }"></div>
        </div>
        <div class="ic-val">{{ mesePassati }}/{{ meseTotali }}</div>
      </div>

      <div class="ic-row">
        <div class="ic-lbl">
          <span class="ic-dot" style="background:#8b5cf6;"></span>
          <span>Settimana</span>
        </div>
        <div class="ic-bar-wrap">
          <div class="ic-bar" :style="{ width: settimanaPct + '%', background: '#8b5cf6' }"></div>
        </div>
        <div class="ic-val">{{ settimanaCor }}/52</div>
      </div>

      <div class="ic-row">
        <div class="ic-lbl">
          <span class="ic-dot" style="background:#34d399;"></span>
          <span>Budget mensile</span>
        </div>
        <div class="ic-bar-wrap">
          <div class="ic-bar" :style="{ width: budgetPct + '%', background: '#34d399' }"></div>
        </div>
        <div class="ic-val">{{ formatEuro(budgetSpeso) }} / {{ formatEuro(budgetTot) }}</div>
      </div>

      <div class="ic-row">
        <div class="ic-lbl">
          <span class="ic-dot" style="background:#38bdf8;"></span>
          <span>Anno fiscale</span>
        </div>
        <div class="ic-bar-wrap">
          <div class="ic-bar" :style="{ width: annoPct + '%', background: '#38bdf8' }"></div>
        </div>
        <div class="ic-val">{{ annoPct }}%</div>
      </div>

      <div class="ic-row">
        <div class="ic-lbl">
          <span class="ic-dot" style="background:#f472b6;"></span>
          <span>TFR maturato</span>
        </div>
        <div class="ic-bar-wrap">
          <div class="ic-bar" :style="{ width: tfrPct + '%', background: '#f472b6' }"></div>
        </div>
        <div class="ic-val">{{ formatEuro(tfrTot) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  contratti: { type: Array, default: () => [] },
  scadenze: { type: Array, default: () => [] },
})

// --- Stima contributi trimestrale ---
const contributiTot = computed(() => {
  let tot = 0
  for (const c of props.contratti) {
    if (c.stato !== 'ATTIVO') continue
    const val = parseFloat(c.stima_trimestrale) || (parseFloat(c.budget_di_partenza) || 0) * 0.32
    tot += val
  }
  return tot
})

const contributiPct = computed(() => {
  const max = 3000
  return Math.min(Math.round((contributiTot.value / max) * 100), 100)
})

// --- Prossima scadenza contributi ---
const prossimaScadenza = computed(() => props.scadenze.find(s => s.tipo === 'contributo') || null)

const scadenzaGiorni = computed(() => prossimaScadenza.value?.giorni ?? -1)

const scadenzaLabel = computed(() => {
  const s = prossimaScadenza.value
  return s ? s.label : 'Nessuna scadenza'
})

const scadenzaColore = computed(() => {
  const g = scadenzaGiorni.value
  if (g <= 0) return '#f87171'
  if (g <= 7) return '#f59e0b'
  if (g <= 14) return '#eab308'
  return '#34d399'
})

const scadenzaPct = computed(() => {
  const g = scadenzaGiorni.value
  if (g <= 0) return 0
  const maxG = 30
  return Math.min(Math.round((g / maxG) * 100), 100)
})

// --- Fine mese ---
const ora = new Date()
const mesePassati = ora.getDate()
const meseTotali = new Date(ora.getFullYear(), ora.getMonth() + 1, 0).getDate()
const mesePct = Math.round((mesePassati / meseTotali) * 100)

// --- Settimana ISO ---
function getISOWeek(d) {
  const t = new Date(d.valueOf())
  const day = (d.getDay() + 6) % 7
  t.setDate(t.getDate() - day + 3)
  const firstThu = t.valueOf()
  t.setMonth(0, 1)
  if (t.getDay() !== 4) t.setMonth(0, 1 + ((4 - t.getDay()) + 7) % 7)
  return 1 + Math.ceil((firstThu - t.valueOf()) / 604800000)
}
const settimanaCor = getISOWeek(ora)
const settimanaPct = Math.round((settimanaCor / 52) * 100)

// --- Budget mensile progressivo ---
const attivi = computed(() => props.contratti.filter(c => c.stato === 'ATTIVO'))

const budgetTot = computed(() => {
  let tot = 0
  for (const c of attivi.value) tot += parseFloat(c.budget_di_partenza) || 0
  return tot
})

const budgetSpeso = computed(() => {
  const gg = new Date()
  const giorno = gg.getDate()
  const giorniMese = new Date(gg.getFullYear(), gg.getMonth() + 1, 0).getDate()
  let tot = 0
  for (const c of attivi.value) {
    const bgt = parseFloat(c.budget_di_partenza) || 0
    tot += (bgt / giorniMese) * giorno
  }
  return tot
})

const budgetPct = computed(() => {
  if (budgetTot.value <= 0) return 0
  return Math.min(Math.round((budgetSpeso.value / budgetTot.value) * 100), 100)
})

// --- Anno fiscale ---
const giornoAnno = Math.ceil((ora - new Date(ora.getFullYear(), 0, 1)) / 86400000)
const giorniAnno = ((ora.getFullYear() % 4 === 0 && ora.getFullYear() % 100 !== 0) || ora.getFullYear() % 400 === 0) ? 366 : 365
const annoPct = Math.round((giornoAnno / giorniAnno) * 100)

// --- TFR maturato ---
const tfrTot = computed(() => {
  let tot = 0
  const mesi = ora.getMonth() + 1
  for (const c of attivi.value) {
    const bgt = parseFloat(c.budget_di_partenza) || 0
    tot += (bgt / 13.5) * mesi
  }
  return tot
})

const tfrPct = computed(() => {
  if (attivi.value.length === 0) return 0
  const max = 2000 * attivi.value.length
  return Math.min(Math.round((tfrTot.value / max) * 100), 100)
})

// --- helpers ---
function formatEuro(val) {
  if (val == null) return '—'
  return '€ ' + Number(val).toLocaleString('it-IT', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}
</script>

<style scoped>
.ic-card {
  border: 1px solid #1E1E20;
  border-radius: 8px;
  padding: 14px;
  background: transparent;
}
.ic-heading {
  font-size: 12px;
  font-weight: 500;
  color: #E8E8ED;
  margin-bottom: 10px;
}
.ic-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ic-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 6px;
  align-items: center;
  min-height: 24px;
}
.ic-lbl {
  font-size: 11px;
  color: #8A8F98;
  display: flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}
.ic-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  flex-shrink: 0;
}
.ic-bar-wrap {
  height: 6px;
  background: #1E1E20;
  border-radius: 3px;
  overflow: hidden;
}
.ic-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s ease;
}
.ic-val {
  font-size: 10px;
  color: #E8E8ED;
  font-weight: 500;
  text-align: right;
  min-width: 64px;
  flex-shrink: 0;
}
</style>
