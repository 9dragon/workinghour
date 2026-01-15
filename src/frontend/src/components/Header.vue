<template>
  <header class="app-header">
    <div class="header-left">
      <slot name="left"></slot>
    </div>
    <div class="header-right">
      <slot name="right"></slot>
    </div>
  </header>
</template>

<script setup>
</script>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background-color: #fff;
  border-bottom: 1px solid #e8e8e8;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
</style>
