<template>
  <div class="card-outlined mb-3">
    <div class="card-header">
      <span class="card-title">Anagrafica</span>
      <button class="link-request" @click="$emit('apri-richiesta', 'ANAGRAFICA')">Richiedi modifica</button>
    </div>
    <div class="card-body">
      <div class="field-row">
        <div class="field">
          <div class="field-label">Codice Fiscale</div>
          <div class="field-value">{{ datore.codice_fiscale }}</div>
        </div>
        <div class="field">
          <div class="field-label">Indirizzo</div>
          <div class="field-value">{{ datore.indirizzo || '-' }}</div>
        </div>
        <div class="field">
          <div class="field-label">Comune</div>
          <div class="field-value">{{ datore.comune || '-' }}</div>
        </div>
        <div class="field">
          <div class="field-label">Provincia</div>
          <div class="field-value">{{ datore.provincia || '-' }}</div>
        </div>
        <div class="field">
          <div class="field-label">CAP</div>
          <div class="field-value">{{ datore.cap || '-' }}</div>
        </div>
        <div class="field">
          <div class="field-label">Telefono</div>
          <div class="field-value">{{ datore.telefono || '-' }}</div>
        </div>
      </div>
      <div class="field mt-2">
        <div class="field-label">Email</div>
        <div class="field-value">{{ datore.email || '-' }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ datore: { type: Object, required: true } })
defineEmits(['apri-richiesta'])
</script>

<style scoped>
.card-outlined {
  border: 1px solid #1E1E20;
  border-radius: 8px;
  background: transparent;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #1E1E20;
}
.card-title {
  font-size: 13px;
  font-weight: 500;
  color: #E8E8ED;
}
.link-request {
  background: none;
  border: none;
  font-size: 11px;
  color: #5C5F66;
  cursor: pointer;
  padding: 0;
  transition: color 0.15s;
}
.link-request:hover {
  color: #8A8F98;
}
.card-body {
  padding: 16px;
}
.field-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
@media (max-width: 767px) {
  .field-row { grid-template-columns: 1fr 1fr; gap: 8px; }
}
.field-label {
  font-size: 11px;
  color: #8A8F98;
  margin-bottom: 2px;
}
.field-value {
  font-size: 13px;
  color: #E8E8ED;
}
</style>
