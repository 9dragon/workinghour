<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="layout-aside">
      <div class="logo">
        <el-icon class="logo-icon"><DataBoard /></el-icon>
        <span class="logo-text">工时统计系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        @select="handleMenuSelect"
        class="layout-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-sub-menu index="data">
          <template #title>
            <el-icon><Folder /></el-icon>
            <span>数据管理</span>
          </template>
          <el-menu-item index="/data/import">
            <el-icon><Upload /></el-icon>
            <span>Excel数据导入</span>
          </el-menu-item>
          <el-menu-item index="/data/records">
            <el-icon><List /></el-icon>
            <span>导入记录查看</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="query">
          <template #title>
            <el-icon><Search /></el-icon>
            <span>工时查询</span>
          </template>
          <el-menu-item index="/query/project">
            <el-icon><Document /></el-icon>
            <span>项目维度查询</span>
          </el-menu-item>
          <el-menu-item index="/query/organization">
            <el-icon><OfficeBuilding /></el-icon>
            <span>组织维度查询</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="check">
          <template #title>
            <el-icon><CircleCheck /></el-icon>
            <span>工时核对</span>
          </template>
          <el-menu-item index="/check/integrity">
            <el-icon><Clock /></el-icon>
            <span>完整性检查</span>
          </el-menu-item>
          <el-menu-item index="/check/compliance">
            <el-icon><Warning /></el-icon>
            <span>合规性检查</span>
          </el-menu-item>
          <el-menu-item index="/check/history">
            <el-icon><Notebook /></el-icon>
            <span>核对历史记录</span>
          </el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="layout-main">
      <el-header class="layout-header">
        <div class="header-left">
          <span class="page-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :src="userAvatar">
                {{ userInfo.realName?.charAt(0) || 'U' }}
              </el-avatar>
              <span class="user-name">{{ userInfo.realName || userInfo.userName || '用户' }}</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="layout-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta.title || '工时统计系统')
const userInfo = computed(() => userStore.userInfo)
const userAvatar = computed(() => userInfo.value.avatar || '')

const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}

const handleMenuSelect = (index) => {
  // 只处理以 / 开头的有效路径，过滤掉子菜单的 index
  if (index.startsWith('/')) {
    router.push(index)
  }
}
</script>

<style scoped>
.layout-container {
  width: 100%;
  height: 100vh;
}

.layout-aside {
  background-color: #304156;
  overflow-x: hidden;
  overflow-y: auto;
}

.logo {
  display: flex;
  align-items: center;
  padding: 20px;
  background-color: #2b3a4b;
}

.logo-icon {
  font-size: 24px;
  color: #409EFF;
  margin-right: 10px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.layout-menu {
  border-right: none;
}

.layout-main {
  background-color: #f0f2f5;
}

.layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.header-left .page-title {
  font-size: 20px;
  font-weight: 500;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: #f5f7fa;
}

.user-name {
  margin: 0 8px;
  font-size: 14px;
  color: #606266;
}

.layout-content {
  padding: 24px;
  overflow-y: auto;
}
</style>
