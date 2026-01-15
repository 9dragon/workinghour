<template>
  <aside class="app-sidebar">
    <div class="sidebar-header">
      <h2>{{ title }}</h2>
    </div>
    <nav class="sidebar-nav">
      <slot></slot>
    </nav>
  </aside>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '菜单'
  }
})
</script>

<style scoped>
.app-sidebar {
  width: 240px;
  background-color: #001529;
  color: #fff;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 0;
}
</style>
