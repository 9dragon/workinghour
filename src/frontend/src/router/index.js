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
        path: 'data/employee-management',
        name: 'EmployeeManagement',
        component: () => import('@/views/EmployeeManagement.vue'),
        meta: { title: '员工管理' }
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
        meta: { title: '周报提交检查' }
      },
      {
        path: 'check/hours',
        name: 'WorkHoursCheck',
        component: () => import('@/views/WorkHoursCheck.vue'),
        meta: { title: '工作时长检查' }
      },
      {
        path: 'check/history',
        name: 'CheckHistory',
        component: () => import('@/views/CheckHistory.vue'),
        meta: { title: '核对历史' }
      },
      {
        path: 'check/detail/:checkNo',
        name: 'CheckDetail',
        component: () => import('@/views/CheckDetail.vue'),
        meta: { title: '核对详情' }
      },
      {
        path: 'check/holidays',
        name: 'HolidayManagement',
        component: () => import('@/views/HolidayManagement.vue'),
        meta: { title: '节假日管理' }
      },
      {
        path: 'system/user-management',
        name: 'UserManagement',
        component: () => import('@/views/SystemUserManagement.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'user-management',
        redirect: '/data/employee-management'
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
