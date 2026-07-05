<template>
  <TeleportModal v-model="aperto" max-width="480">
    <div class="modal-card">
      <div class="modal-title">Richiedi modifica</div>
      <div class="modal-body">

        <div v-if="errore" class="msg-error mb-3">{{ errore }}</div>
        <div v-if="successo" class="msg-success mb-3">{{ successo }}</div>

        <select v-model="tipo" class="modal-input mb-3" required>
          <option value="" disabled>Tipo richiesta</option>
          <option v-for="t in tipiRichiesta" :key="t.value" :value="t.value">{{ t.text }}</option>
        </select>

        <template v-if="tipo === 'ANAGRAFICA'">
          <select v-model="campo" class="modal-input mb-3">
            <option value="" disabled>Campo</option>
            <option v-for="c in campiAnagrafica" :key="c.value" :value="c.value">{{ c.text }}</option>
          </select>
          <input v-model="nuovoValore" placeholder="Nuovo valore" class="modal-input mb-3" />
        </template>
        <template v-else-if="tipo === 'CONTRATTO'">
          <select v-model="campo" class="modal-input mb-3">
            <option value="" disabled>Campo contratto</option>
            <option v-for="c in campiContratto" :key="c.value" :value="c.value">{{ c.text }}</option>
          </select>
          <input v-model="nuovoValore" placeholder="Nuovo valore" class="modal-input mb-3" />
        </template>
        <template v-else-if="tipo === 'PROGETTO'">
          <textarea v-model="nuovoValore" placeholder="Descrivi le modifiche ai progetti" class="modal-textarea mb-3"></textarea>
        </template>
        <template v-else-if="tipo && tipo !== 'ANAGRAFICA' && tipo !== 'CONTRATTO' && tipo !== 'PROGETTO'">
          <div class="modal-hint">Spiega la tua richiesta nel campo "Nota".</div>
        </template>

        <textarea v-model="nota" placeholder="Nota per l'amministratore (facoltativa)" class="modal-textarea" rows="2"></textarea>
      </div>
      <div class="modal-actions">
        <button type="button" class="modal-btn-cancel" @click="chiudi">Annulla</button>
        <button type="button" class="modal-btn-primary" :disabled="!tipo || caricamento" @click="invia">
          {{ caricamento ? 'Invio in corso...' : 'Invia richiesta' }}
        </button>
      </div>
    </div>
  </TeleportModal>
</template>

<script setup>
import { ref, watch } from 'vue'
import client from '../api/client'
import TeleportModal from './TeleportModal.vue'

const props = defineProps({
  modelValue: Boolean,
})
const emit = defineEmits(['update:modelValue', 'inviata'])

const aperto = ref(props.modelValue)
watch(() => props.modelValue, (v) => { aperto.value = v })
watch(aperto, (v) => {
  emit('update:modelValue', v)
  if (!v) { resetForm() }
})

const tipiRichiesta = [
  { text: 'Modifica Anagrafica', value: 'ANAGRAFICA' },
  { text: 'Modifica Contratto', value: 'CONTRATTO' },
  { text: 'Modifica Progetto', value: 'PROGETTO' },
  { text: 'Richiesta Cessazione', value: 'CESSAZIONE' },
  { text: 'Richiesta Malattia / Sostituzione', value: 'MALATTIA' },
  { text: 'Richiesta Certificazione Unica', value: 'CU' },
  { text: 'Altro (testo libero)', value: 'TESTO_LIBERO' },
]

const campiAnagrafica = [
  { text: 'Indirizzo', value: 'indirizzo' },
  { text: 'Comune', value: 'comune' },
  { text: 'Email', value: 'email' },
  { text: 'Telefono', value: 'telefono' },
]

const campiContratto = [
  { text: 'Ore settimanali', value: 'ore_settimanali' },
  { text: 'Paga oraria lorda', value: 'paga_oraria_lorda' },
  { text: 'Lordo mensile (budget)', value: 'budget_mensile' },
]

const tipo = ref('')
const campo = ref('')
const nuovoValore = ref('')
const nota = ref('')
const errore = ref('')
const successo = ref('')
const caricamento = ref(false)

function resetForm() {
  tipo.value = ''
  campo.value = ''
  nuovoValore.value = ''
  nota.value = ''
  errore.value = ''
  successo.value = ''
}

async function invia() {
  if (!tipo.value) return
  caricamento.value = true
  errore.value = ''
  successo.value = ''
  try {
    await client.post('/richieste/', {
      tipo: tipo.value,
      campo: campo.value,
      etichetta: campo.value || '',
      valore_richiesto: nuovoValore.value,
      nota: nota.value,
    })
    successo.value = 'Richiesta inviata con successo!'
    emit('inviata')
    setTimeout(() => { aperto.value = false }, 1500)
  } catch (err) {
    errore.value = err.response?.data?.error || 'Errore durante l\'invio.'
  } finally {
    caricamento.value = false
  }
}

function chiudi() {
  aperto.value = false
}
</script>

<style scoped>
.modal-card {
  background: #131316;
  border: 1px solid #1E1E20;
  border-radius: 8px;
}
.modal-title {
  font-size: 14px;
  font-weight: 500;
  color: #E8E8ED;
  padding: 16px 20px 8px;
}
.modal-body {
  padding: 8px 20px;
}
.modal-actions {
  padding: 8px 20px 16px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.modal-input {
  width: 100%;
  background: #09090B;
  border: 1px solid #2A2A2E;
  border-radius: 6px;
  color: #E8E8ED;
  font-size: 12px;
  padding: 6px 10px;
  outline: none;
  height: 32px;
  box-sizing: border-box;
}
.modal-input:focus {
  border-color: #5E6AD2;
}
.modal-textarea {
  width: 100%;
  background: #09090B;
  border: 1px solid #2A2A2E;
  border-radius: 6px;
  color: #E8E8ED;
  font-size: 12px;
  padding: 6px 10px;
  outline: none;
  box-sizing: border-box;
  resize: vertical;
  font-family: inherit;
}
.modal-textarea:focus {
  border-color: #5E6AD2;
}
.modal-btn-cancel {
  background: none;
  border: none;
  color: #5C5F66;
  font-size: 12px;
  cursor: pointer;
  padding: 6px 12px;
}
.modal-btn-cancel:hover {
  color: #8A8F98;
}
.modal-btn-primary {
  background: #E8E8ED;
  color: #09090B;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  font-size: 12px;
  height: 32px;
  padding: 0 16px;
  cursor: pointer;
}
.modal-btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.modal-hint {
  font-size: 12px;
  color: #8A8F98;
  margin-bottom: 12px;
}
.msg-error {
  background: rgba(248,113,113,0.1);
  border: 1px solid rgba(248,113,113,0.3);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 12px;
  color: #f87171;
}
.msg-success {
  background: rgba(52,211,153,0.1);
  border: 1px solid rgba(52,211,153,0.3);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 12px;
  color: #34d399;
}
.mb-3 { margin-bottom: 12px; }
</style>
