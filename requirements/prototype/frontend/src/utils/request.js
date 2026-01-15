import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store'

// 模拟模式：用于无后端时体验前端原型
const MOCK_MODE = true

// 创建 axios 实例
const request = axios.create({
  baseURL: 'http://localhost:8000/api', // 后端 API 地址
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code === 200) {
      return res
    } else {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
  },
  (error) => {
    // 模拟模式下，返回模拟数据
    if (MOCK_MODE && error.code === 'ERR_NETWORK') {
      console.log('[Mock Mode] 返回模拟响应')
      return Promise.reject(new Error('MOCK_MODE_NETWORK_ERROR'))
    }

    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 401:
          ElMessage.error('登录已过期，请重新登录')
          const userStore = useUserStore()
          userStore.logout()
          window.location.href = '/login'
          break
        case 403:
          ElMessage.error('没有权限访问')
          break
        case 500:
          ElMessage.error(data.message || '服务器错误')
          break
        default:
          ElMessage.error(data.message || '请求失败')
      }
    } else {
      ElMessage.error('网络连接失败')
    }
    return Promise.reject(error)
  }
)

// 导出 MOCK_MODE 供 API 模块使用
export { MOCK_MODE }

export default request
