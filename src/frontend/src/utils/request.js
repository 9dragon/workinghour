import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store'

// 模拟模式：用于无后端时体验前端原型
const MOCK_MODE = false

// 创建 axios 实例
const request = axios.create({
  // 开发环境使用 http://localhost:8000/api/v1（通过 .env.development 配置）
  // 生产环境使用相对路径 /api/v1（通过 nginx 反向代理到后端）
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
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
    // 如果是blob类型（文件下载），直接返回response.data
    if (response.config.responseType === 'blob') {
      return response.data
    }

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

      // 如果是blob响应的错误，需要读取错误信息
      if (error.config?.responseType === 'blob' && data instanceof Blob) {
        return new Promise((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => {
            try {
              const errorData = JSON.parse(reader.result)
              ElMessage.error(errorData.message || '请求失败')
              reject(error)
            } catch {
              ElMessage.error('文件下载失败')
              reject(error)
            }
          }
          reader.onerror = () => {
            ElMessage.error('文件下载失败')
            reject(error)
          }
          reader.readAsText(data)
        })
      }

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
