/**
 * 钉钉免登录工具
 *
 * 使用方法：
 * 1. 在钉钉客户端中打开应用
 * 2. 调用 dingtalkLogin() 进行免登录
 * 3. 自动获取用户信息并返回JWT token
 */

import axios from 'axios'

const API_BASE = '/api/v1/auth'

/**
 * 检测是否在钉钉环境中
 * @returns {boolean}
 */
export function isDingTalkEnv() {
  const ua = navigator.userAgent
  return /dingtalk/i.test(ua) || /DingTalk/i.test(ua)
}

/**
 * 获取免登授权码
 * @param {string} corpId - 企业ID
 * @returns {Promise<string>}
 */
export function getDingTalkAuthCode(corpId) {
  return new Promise((resolve, reject) => {
    // 检查 dd 对象是否存在
    if (typeof dd === 'undefined') {
      reject(new Error('钉钉JSAPI未加载，请在钉钉客户端中打开'))
      return
    }

    // 调用钉钉JSAPI获取授权码
    dd.runtime.permission.requestAuthCode({
      corpId: corpId,
      success: (result) => {
        console.log('获取钉钉授权码成功:', result)
        resolve(result.code)
      },
      fail: (err) => {
        console.error('获取钉钉授权码失败:', err)
        reject(new Error(err.errorMessage || '获取授权码失败'))
      }
    })
  })
}

/**
 * 钉钉免登录
 * @param {string} authCode - 钉钉授权码
 * @returns {Promise<Object>} 登录响应数据
 */
export async function dingtalkLogin(authCode) {
  try {
    const response = await axios.post(`${API_BASE}/dingtalk/login`, {
      authCode
    })

    if (response.data.code === 0) {
      return response.data
    } else {
      throw new Error(response.data.message || '登录失败')
    }
  } catch (error) {
    console.error('钉钉免登录请求失败:', error)
    throw error
  }
}

/**
 * 自动执行钉钉免登录流程
 * @param {string} corpId - 企业ID（可选，从配置获取）
 * @returns {Promise<Object>} 登录响应数据
 */
export async function autoDingtalkLogin(corpId) {
  try {
    // 1. 获取授权码
    const authCode = await getDingTalkAuthCode(corpId)

    // 2. 发送到后端验证并获取token
    const response = await dingtalkLogin(authCode)

    return response
  } catch (error) {
    console.error('钉钉自动登录失败:', error)
    throw error
  }
}

/**
 * 获取钉钉配置信息
 * @returns {Promise<Object>} 钉钉配置
 */
export async function getDingTalkConfig() {
  try {
    const response = await axios.get(`${API_BASE}/dingtalk/config`)
    return response.data.data
  } catch (error) {
    console.error('获取钉钉配置失败:', error)
    throw error
  }
}

/**
 * 钉钉JSAPI初始化（如需使用其他钉钉功能）
 * @param {Object} config - 配置对象
 * @returns {Promise<void>}
 */
export function initDingTalkJSAPI(config) {
  return new Promise((resolve, reject) => {
    if (typeof dd === 'undefined') {
      reject(new Error('钉钉JSAPI未加载'))
      return
    }

    dd.config({
      agentId: config.agentId || '',
      corpId: config.corpId || '',
      timeStamp: config.timeStamp,
      nonceStr: config.nonceStr,
      signature: config.signature,
      type: 0,
      jsApiList: config.jsApiList || [
        'runtime.permission.requestAuthCode',
        'device.notification.confirm',
        'device.notification.alert'
      ]
    })

    dd.ready(() => {
      console.log('钉钉JSAPI初始化成功')
      resolve()
    })

    dd.error((err) => {
      console.error('钉钉JSAPI初始化失败:', err)
      reject(err)
    })
  })
}

/**
 * 保存登录信息到本地存储
 * @param {Object} data - 登录响应数据
 */
export function saveLoginInfo(data) {
  const { token, userInfo } = data

  // 保存token
  localStorage.setItem('token', token)
  localStorage.setItem('tokenType', 'Bearer')

  // 保存用户信息
  localStorage.setItem('userInfo', JSON.stringify(userInfo))
  localStorage.setItem('userName', userInfo.userName)
  localStorage.setItem('userRole', userInfo.role)

  // 设置登录时间
  localStorage.setItem('loginTime', Date.now().toString())
}

/**
 * 清除登录信息
 */
export function clearLoginInfo() {
  localStorage.removeItem('token')
  localStorage.removeItem('tokenType')
  localStorage.removeItem('userInfo')
  localStorage.removeItem('userName')
  localStorage.removeItem('userRole')
  localStorage.removeItem('loginTime')
}

/**
 * 检查是否已登录
 * @returns {boolean}
 */
export function isLoggedIn() {
  const token = localStorage.getItem('token')
  const loginTime = localStorage.getItem('loginTime')

  if (!token || !loginTime) {
    return false
  }

  // 检查token是否过期（8小时）
  const now = Date.now()
  const elapsed = now - parseInt(loginTime)
  const maxAge = 8 * 60 * 60 * 1000 // 8小时

  return elapsed < maxAge
}

/**
 * 获取当前用户信息
 * @returns {Object|null}
 */
export function getCurrentUser() {
  const userInfoStr = localStorage.getItem('userInfo')
  if (!userInfoStr) {
    return null
  }

  try {
    return JSON.parse(userInfoStr)
  } catch (error) {
    console.error('解析用户信息失败:', error)
    return null
  }
}

/**
 * 钉钉免登录完整流程
 * @param {Object} options - 配置选项
 * @param {Function} options.onSuccess - 登录成功回调
 * @param {Function} options.onError - 登录失败回调
 * @param {Function} options.onLoading - 加载状态回调
 */
export async function dingtalkLoginFlow(options = {}) {
  const { onSuccess, onError, onLoading } = options

  try {
    // 更新加载状态
    onLoading && onLoading(true)

    // 1. 检查环境
    if (!isDingTalkEnv()) {
      throw new Error('请在钉钉客户端中打开此页面')
    }

    // 2. 获取钉钉配置
    const config = await getDingTalkConfig()

    // 3. 执行自动登录
    const response = await autoDingtalkLogin(config.corpId)

    // 4. 保存登录信息
    saveLoginInfo(response.data)

    // 5. 成功回调
    onSuccess && onSuccess(response.data)

    return response.data
  } catch (error) {
    console.error('钉钉登录流程失败:', error)

    // 失败回调
    onError && onError(error)

    throw error
  } finally {
    // 结束加载状态
    onLoading && onLoading(false)
  }
}

// 默认导出
export default {
  isDingTalkEnv,
  getDingTalkAuthCode,
  dingtalkLogin,
  autoDingtalkLogin,
  getDingTalkConfig,
  initDingTalkJSAPI,
  saveLoginInfo,
  clearLoginInfo,
  isLoggedIn,
  getCurrentUser,
  dingtalkLoginFlow
}
