import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/components/Layout.vue'),
    redirect: '/data/import',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'data/import',
        name: 'DataImport',
        component: () => import('@/views/DataImport.vue'),
        meta: { title: 'Excel数据导入' }
      },
      {
        path: 'data/records',
        name: 'ImportRecords',
        component: () => import('@/views/ImportRecords.vue'),
        meta: { title: '导入记录查看' }
      },
      {
        path: 'data/records/:batchNo/view',
        name: 'ImportDataView',
        component: () => import('@/views/ImportDataView.vue'),
        meta: { title: '导入数据查看' }
      },
      {
        path: 'query/project',
        name: 'ProjectQuery',
        component: () => import('@/views/ProjectQuery.vue'),
        meta: { title: '项目维度查询' }
      },
      {
        path: 'query/organization',
        name: 'OrganizationQuery',
        component: () => import('@/views/OrganizationQuery.vue'),
        meta: { title: '组织维度查询' }
      },
      {
        path: 'check/integrity',
        name: 'IntegrityCheck',
        component: () => import('@/views/IntegrityCheck.vue'),
        meta: { title: '工时完整性检查' }
      },
      {
        path: 'check/compliance',
        name: 'ComplianceCheck',
        component: () => import('@/views/ComplianceCheck.vue'),
        meta: { title: '工时合规性检查' }
      },
      {
        path: 'check/history',
        name: 'CheckHistory',
        component: () => import('@/views/CheckHistory.vue'),
        meta: { title: '核对历史记录' }
      },
      {
        path: 'settings',
        name: 'SystemSettings',
        component: () => import('@/views/SystemSettings.vue'),
        meta: { title: '系统设置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 登录验证
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && userStore.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
