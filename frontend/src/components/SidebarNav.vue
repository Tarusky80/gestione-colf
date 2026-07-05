<template>
  <nav class="sidebar">
    <div class="sidebar-top">
      <button class="sidebar-btn" :class="{ active: routeName === 'Dashboard' }" @click="go('Dashboard')" title="Dashboard">
        <AppIcon name="dashboard" />
        <span class="sidebar-label">Dashboard</span>
      </button>
    </div>
    <div class="sidebar-bottom">
      <button class="sidebar-btn sidebar-btn-logout" @click="logout" title="Esci">
        <AppIcon name="logout" />
        <span class="sidebar-label">Esci</span>
      </button>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AppIcon from './AppIcon.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const routeName = computed(() => route.name)

function go(name) { router.push({ name }) }
function logout() { auth.logout(); router.push('/login') }
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 56px;
  height: 100vh;
  background: #09090B;
  border-right: 1px solid #1E1E20;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  z-index: 1000;
}
.sidebar-top, .sidebar-bottom {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.sidebar-btn {
  width: 36px;
  height: 36px;
  color: #5C5F66;
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: color 0.15s, background 0.15s;
}
.sidebar-btn:hover { color: #E8E8ED; }
.sidebar-btn.active { color: #E8E8ED; }
.sidebar-btn-logout:hover { background: rgba(248,113,113,0.15) !important; }
.sidebar-label { display: none; }

@media (max-width: 767px) {
  .sidebar {
    top: auto;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 56px;
    flex-direction: row;
    border-right: none;
    border-top: 1px solid #1E1E20;
    padding: 0 16px;
  }
  .sidebar-top, .sidebar-bottom {
    flex-direction: row;
    gap: 0;
  }
  .sidebar-btn {
    width: 48px;
    height: 48px;
  }
  .sidebar-label { display: inline; font-size: 9px; }
}
</style>
