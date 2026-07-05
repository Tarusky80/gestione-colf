<template>
  <Teleport to="body">
    <div v-if="visibile" class="toast" :style="{ background: bgColor }">
      {{ messaggio }}
    </div>
  </Teleport>
</template>

<script setup>
import { watch, ref } from 'vue'

const props = defineProps({
  visibile: Boolean,
  messaggio: String,
  colore: { type: String, default: 'success' },
})
const emit = defineEmits(['update:visibile'])

const bgColor = ref('#22c55e')

watch(() => props.colore, (c) => {
  bgColor.value = { success: '#22c55e', error: '#f87171', warning: '#f59e0b', info: '#38bdf8' }[c] || '#22c55e'
}, { immediate: true })

let timer = null
watch(() => props.visibile, (v) => {
  if (timer) clearTimeout(timer)
  if (v) {
    timer = setTimeout(() => {
      emit('update:visibile', false)
    }, 3000)
  }
})
</script>

<style scoped>
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  color: #fff;
  font-size: 13px;
  padding: 10px 20px;
  border-radius: 6px;
  z-index: 3000;
  animation: toast-in 0.2s ease;
}
@keyframes toast-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
