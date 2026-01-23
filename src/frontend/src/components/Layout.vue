<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapsed ? '64px' : '220px'" class="layout-aside">
      <div class="logo">
        <el-icon class="logo-icon"><DataBoard /></el-icon>
        <span v-show="!isCollapsed" class="logo-text">工时统计系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
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
            <span>周报提交完整性检查</span>
          </el-menu-item>
          <el-menu-item index="/check/hours">
            <el-icon><Warning /></el-icon>
            <span>工作时长一致性检查</span>
          </el-menu-item>
          <el-menu-item index="/check/holidays">
            <el-icon><Calendar /></el-icon>
            <span>节假日管理</span>
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
          <el-icon class="hamburger-icon" @click="toggleSidebar">
            <Expand v-if="isCollapsed" />
            <Fold v-else />
          </el-icon>
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
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapsed = ref(false)

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

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
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
  transition: width 0.3s ease;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background-color: #2b3a4b;
  transition: padding 0.3s ease;
}

.logo-icon {
  font-size: 24px;
  color: #409EFF;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin-left: 10px;
  white-space: nowrap;
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

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hamburger-icon {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
  transition: color 0.3s;
}

.hamburger-icon:hover {
  color: #409EFF;
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
