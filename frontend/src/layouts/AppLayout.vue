<template>
  <div class="layout">
    <SidebarNav />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import SidebarNav from '../components/SidebarNav.vue'
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
  background: #09090B;
}
.main-content {
  margin-left: 56px;
  flex: 1;
  min-width: 0;
}
@media (max-width: 767px) {
  .main-content {
    margin-left: 0;
    margin-bottom: 56px;
  }
}
</style>
