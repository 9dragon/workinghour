<template>
  <div class="system-settings-page">
    <el-row :gutter="20">
      <!-- 数据备份与恢复 -->
      <el-col :span="12">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <el-icon><Download /></el-icon>
              <span>数据备份与恢复</span>
            </div>
          </template>

          <div class="backup-section">
            <el-alert title="提示" type="info" :closable="false" style="margin-bottom: 20px">
              建议定期备份系统数据，以防数据丢失。备份文件为 SQLite 数据库文件格式，可使用恢复功能进行数据还原。
            </el-alert>

            <div class="backup-actions">
              <div class="backup-action">
                <div class="action-title">数据备份</div>
                <el-button type="primary" :loading="backingUp" @click="handleBackup">
                  <el-icon><Download /></el-icon>
                  执行备份
                </el-button>
                <p class="action-desc">将系统当前数据导出为 SQLite 数据库备份文件</p>
              </div>

              <el-divider />

              <div class="backup-action">
                <div class="action-title">数据恢复</div>
                <el-upload
                  ref="uploadRef"
                  :auto-upload="false"
                  :on-change="handleFileChange"
                  :limit="1"
                  accept=".db"
                  style="width: 100%"
                >
                  <el-button type="warning">
                    <el-icon><Upload /></el-icon>
                    选择备份文件
                  </el-button>
                </el-upload>
                <p v-if="selectedBackupFile" class="selected-file">
                  已选择: {{ selectedBackupFile.name }}
                </p>
                <el-button
                  v-if="selectedBackupFile"
                  type="warning"
                  :loading="restoring"
                  @click="handleRestore"
                >
                  开始恢复
                </el-button>
                <p class="action-desc">从 SQLite 数据库备份文件恢复系统数据（会覆盖当前数据）</p>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 系统配置 -->
      <el-col :span="12">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>系统配置</span>
            </div>
          </template>

          <el-form :model="systemConfig" label-width="140px" class="config-form">
            <el-form-item label="文件保留周期">
              <el-input-number v-model="systemConfig.fileRetentionDays" :min="1" :max="365" />
              <span style="margin-left: 8px">天</span>
            </el-form-item>

            <el-form-item label="最大导入行数">
              <el-input-number v-model="systemConfig.maxImportRows" :min="100" :max="10000" :step="100" />
              <span style="margin-left: 8px">行</span>
            </el-form-item>

            <el-form-item label="最大文件大小">
              <el-input-number v-model="systemConfig.maxFileSize" :min="1" :max="100" />
              <span style="margin-left: 8px">MB</span>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleSaveConfig">
                <el-icon><Check /></el-icon>
                保存配置
              </el-button>
              <el-button @click="handleResetConfig">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 定时检查与通知 -->
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <el-icon><Bell /></el-icon>
          <span>定时检查与通知</span>
          <el-tag v-if="schedulerConfig.reloadPending" type="warning" size="small" style="margin-left: auto">
            有未生效的修改（≤60s 自动重载）
          </el-tag>
        </div>
      </template>

      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        定时任务由独立调度器进程执行。修改后无需重启服务，调度器会在 60 秒内自动重载。
        发送对象为员工本人（钉钉按手机号 @人，邮件按员工邮箱）。
      </el-alert>

      <el-form :model="schedulerConfig" label-width="140px" class="config-form">
        <el-form-item label="启用定时检查">
          <el-switch v-model="schedulerConfig.schedulerEnabled" />
        </el-form-item>

        <el-form-item label="执行频率">
          <el-radio-group v-model="cronPreset" @change="onPresetChange">
            <el-radio label="weekly_mon">每周一</el-radio>
            <el-radio label="weekly_fri">每周五</el-radio>
            <el-radio label="daily">每天</el-radio>
            <el-radio label="custom">自定义</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="执行时间">
          <el-time-picker
            v-model="schedulerTime"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="选择时间"
            @change="onTimeChange"
          />
        </el-form-item>

        <el-form-item v-if="cronPreset === 'custom'" label="Cron 表达式">
          <el-input
            v-model="schedulerConfig.schedulerCron"
            placeholder="5 字段：分 时 日 月 周，如 0 18 * * 1"
            style="width: 280px"
          />
          <span class="hint-text">分 时 日 月 周</span>
        </el-form-item>

        <el-form-item label="时区">
          <el-select v-model="schedulerConfig.schedulerTimezone" style="width: 220px">
            <el-option label="Asia/Shanghai (北京)" value="Asia/Shanghai" />
            <el-option label="Asia/Tokyo (东京)" value="Asia/Tokyo" />
            <el-option label="UTC" value="UTC" />
          </el-select>
        </el-form-item>

        <el-form-item label="检查窗口">
          <el-input-number v-model="schedulerConfig.lookbackWeeks" :min="1" :max="12" />
          <span style="margin-left: 8px">周（往前推 N 周的工时数据）</span>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="savingScheduler" @click="saveSchedulerConfig">
            保存配置
          </el-button>
          <el-button :loading="reloading" @click="reloadSchedulerNow">
            立即重载调度器
          </el-button>
          <el-button type="warning" :loading="testing" @click="triggerTest">
            手动触发一次测试
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 钉钉配置 -->
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <el-icon><ChatDotRound /></el-icon>
          <span>钉钉渠道配置</span>
          <el-tag
            :type="dingtalkConfig.configured ? 'success' : 'danger'"
            size="small"
            style="margin-left: auto"
          >
            {{ dingtalkConfig.configured ? '凭证完整' : '凭证缺失' }}
          </el-tag>
        </div>
      </template>

      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        凭证需在钉钉开放平台企业应用后台获取。AppSecret 输入框留空表示不修改现有值；
        一旦填写即覆盖。所有字段保存后立即生效，下一次定时检查会自动使用新凭证。
      </el-alert>

      <el-form :model="dingtalkConfig" label-width="120px" class="config-form">
        <el-form-item label="启用钉钉">
          <el-switch v-model="dingtalkConfig.enabled" />
        </el-form-item>
        <el-form-item label="CorpID">
          <el-input v-model="dingtalkConfig.corpId" placeholder="企业 CorpID" style="width: 320px" />
        </el-form-item>
        <el-form-item label="AgentId">
          <el-input v-model="dingtalkConfig.agentId" placeholder="企业应用 AgentId" style="width: 320px" />
        </el-form-item>
        <el-form-item label="AppKey">
          <el-input v-model="dingtalkConfig.appKey" placeholder="企业应用 AppKey" style="width: 320px" />
        </el-form-item>
        <el-form-item label="AppSecret">
          <el-input
            v-model="dingtalkConfig.appSecret"
            type="password"
            show-password
            :placeholder="dingtalkConfig.hasAppSecret ? '•••••••• (留空表示不修改)' : '请输入 AppSecret'"
            style="width: 320px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="savingDingtalk" @click="saveDingtalkConfig">
            保存配置
          </el-button>
        </el-form-item>

        <el-divider content-position="left">发送测试</el-divider>
        <el-form-item label="测试接收手机">
          <el-input v-model="dingtalkTestTarget" placeholder="11 位手机号" style="width: 200px" />
          <el-button
            type="warning"
            :loading="testingDingtalk"
            :disabled="!dingtalkTestTarget"
            style="margin-left: 8px"
            @click="testDingtalk"
          >
            发送测试消息
          </el-button>
          <span class="hint-text">会真实发送一条钉钉消息</span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 邮件配置 -->
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <el-icon><Message /></el-icon>
          <span>邮件渠道配置</span>
          <el-tag
            :type="emailConfig.configured ? 'success' : 'danger'"
            size="small"
            style="margin-left: auto"
          >
            {{ emailConfig.configured ? '凭证完整' : '凭证缺失' }}
          </el-tag>
        </div>
      </template>

      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        支持 SMTP / SMTPS。密码输入框留空表示不修改现有值。常见端口：SSL=465，STARTTLS=587。
      </el-alert>

      <el-form :model="emailConfig" label-width="120px" class="config-form">
        <el-form-item label="启用邮件">
          <el-switch v-model="emailConfig.enabled" />
        </el-form-item>
        <el-form-item label="SMTP 主机">
          <el-input v-model="emailConfig.host" placeholder="如 smtp.example.com" style="width: 320px" />
        </el-form-item>
        <el-form-item label="端口">
          <el-input-number v-model="emailConfig.port" :min="1" :max="65535" />
          <el-checkbox v-model="emailConfig.useSsl" style="margin-left: 16px">使用 SSL</el-checkbox>
        </el-form-item>
        <el-form-item label="登录账号">
          <el-input v-model="emailConfig.user" placeholder="SMTP 登录用户名（通常为邮箱地址）" style="width: 320px" />
        </el-form-item>
        <el-form-item label="发件人地址">
          <el-input v-model="emailConfig.fromAddr" placeholder="收件人看到的发件人，一般与登录账号相同" style="width: 320px" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="emailConfig.password"
            type="password"
            show-password
            :placeholder="emailConfig.hasPassword ? '•••••••• (留空表示不修改)' : '请输入 SMTP 密码'"
            style="width: 320px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="savingEmail" @click="saveEmailConfig">
            保存配置
          </el-button>
        </el-form-item>

        <el-divider content-position="left">发送测试</el-divider>
        <el-form-item label="测试收件邮箱">
          <el-input v-model="emailTestTarget" placeholder="如 test@example.com" style="width: 280px" />
          <el-button
            type="warning"
            :loading="testingEmail"
            :disabled="!emailTestTarget"
            style="margin-left: 8px"
            @click="testEmail"
          >
            发送测试邮件
          </el-button>
          <span class="hint-text">会真实发送一封邮件</span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 系统信息 -->
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <el-icon><InfoFilled /></el-icon>
          <span>系统信息</span>
        </div>
      </template>

      <el-descriptions :column="4" border>
        <el-descriptions-item label="系统版本">v1.0.0</el-descriptions-item>
        <el-descriptions-item label="前端框架">Vue.js 3 + Element Plus</el-descriptions-item>
        <el-descriptions-item label="后端框架">Python Flask</el-descriptions-item>
        <el-descriptions-item label="数据库">SQLite 3</el-descriptions-item>
        <el-descriptions-item label="部署环境">
          {{ systemInfo.deployEnv }}
        </el-descriptions-item>
        <el-descriptions-item label="数据统计">
          总记录: {{ systemInfo.totalRecords }}
        </el-descriptions-item>
        <el-descriptions-item label="最近更新">
          {{ systemInfo.lastUpdate }}
        </el-descriptions-item>
        <el-descriptions-item label="服务器时间">
          {{ systemInfo.serverTime }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 确认恢复对话框 -->
    <el-dialog
      v-model="restoreDialogVisible"
      title="确认数据恢复"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-alert
        title="警告"
        type="error"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        数据恢复操作不可撤销，当前系统数据将被完全覆盖！
      </el-alert>
      <p>请确认以下信息：</p>
      <ul>
        <li>备份文件: {{ selectedBackupFile?.name }}</li>
        <li>操作时间: {{ new Date().toLocaleString('zh-CN') }}</li>
      </ul>
      <p style="color: #F56C6C; margin-top: 10px">建议在执行恢复前先备份当前数据！</p>
      <template #footer>
        <el-button @click="restoreDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="restoring" @click="confirmRestore">
          确认恢复
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  backupData, restoreData, getSystemConfig, updateSystemConfig,
  getNotificationConfig, updateSchedulerConfig, reloadScheduler, triggerNotificationTest,
  updateDingtalkConfig, updateEmailConfig, testDingtalkChannel, testEmailChannel
} from '@/api'

const backingUp = ref(false)
const restoring = ref(false)
const restoreDialogVisible = ref(false)
const selectedBackupFile = ref(null)

const systemConfig = reactive({
  fileRetentionDays: 7,
  maxImportRows: 1000,
  maxFileSize: 10
})

const systemInfo = reactive({
  deployEnv: '开发环境',
  totalRecords: 0,
  lastUpdate: '-',
  serverTime: new Date().toLocaleString('zh-CN')
})

// ============== 定时检查与通知 ==============
const schedulerConfig = reactive({
  schedulerEnabled: true,
  schedulerCron: '0 18 * * 1',
  schedulerTimezone: 'Asia/Shanghai',
  lookbackWeeks: 2,
  reloadPending: false
})
const cronPreset = ref('weekly_mon')
const schedulerTime = ref('18:00')
const savingScheduler = ref(false)
const reloading = ref(false)
const testing = ref(false)

// ============== 钉钉渠道 ==============
const dingtalkConfig = reactive({
  enabled: false,
  configured: false,
  corpId: '',
  agentId: '',
  appKey: '',
  hasAppSecret: false,
  appSecret: ''           // 仅用户主动输入时填，保存后立即清空
})
const dingtalkTestTarget = ref('')
const savingDingtalk = ref(false)
const testingDingtalk = ref(false)

// ============== 邮件渠道 ==============
const emailConfig = reactive({
  enabled: false,
  configured: false,
  host: '',
  port: 465,
  useSsl: true,
  user: '',
  fromAddr: '',
  hasPassword: false,
  password: ''            // 仅用户主动输入时填，保存后立即清空
})
const emailTestTarget = ref('')
const savingEmail = ref(false)
const testingEmail = ref(false)

const detectPreset = (cron) => {
  const parts = (cron || '').split(/\s+/)
  if (parts.length !== 5) return 'custom'
  const [m, h, , , dow] = parts
  if (dow === '1' && parts[2] === '*' && parts[3] === '*') return 'weekly_mon'
  if (dow === '5' && parts[2] === '*' && parts[3] === '*') return 'weekly_fri'
  if (dow === '*' && parts[2] === '*' && parts[3] === '*') return 'daily'
  return 'custom'
}

const onPresetChange = (val) => {
  if (val === 'custom') return
  const [hh, mm] = (schedulerTime.value || '18:00').split(':')
  const dowMap = { weekly_mon: '1', weekly_fri: '5', daily: '*' }
  schedulerConfig.schedulerCron = `${mm} ${hh} * * ${dowMap[val]}`
}

const onTimeChange = (val) => {
  if (!val) return
  const [hh, mm] = val.split(':')
  schedulerConfig.schedulerCron = `${mm} ${hh} * * ${schedulerConfig.schedulerCron.split(/\s+/)[4] || '*'}`
}

const loadSchedulerConfig = async () => {
  try {
    const res = await getNotificationConfig()
    const d = res.data || {}
    schedulerConfig.schedulerEnabled = d.schedulerEnabled
    schedulerConfig.schedulerCron = d.schedulerCron
    schedulerConfig.schedulerTimezone = d.schedulerTimezone
    schedulerConfig.lookbackWeeks = d.lookbackWeeks
    schedulerConfig.reloadPending = d.reloadPending

    // 钉钉
    const dt = d.dingtalk || {}
    dingtalkConfig.enabled = dt.enabled
    dingtalkConfig.configured = dt.configured
    dingtalkConfig.corpId = dt.corpId || ''
    dingtalkConfig.agentId = dt.agentId || ''
    dingtalkConfig.appKey = dt.appKey || ''
    dingtalkConfig.hasAppSecret = !!dt.hasAppSecret
    dingtalkConfig.appSecret = ''   // 永远不在 UI 显示已存在的 secret

    // 邮件
    const em = d.email || {}
    emailConfig.enabled = em.enabled
    emailConfig.configured = em.configured
    emailConfig.host = em.host || ''
    emailConfig.port = em.port || 465
    emailConfig.useSsl = em.useSsl
    emailConfig.user = em.user || ''
    emailConfig.fromAddr = em.fromAddr || ''
    emailConfig.hasPassword = !!em.hasPassword
    emailConfig.password = ''

    cronPreset.value = detectPreset(d.schedulerCron)
    const parts = (d.schedulerCron || '').split(/\s+/)
    if (parts.length === 5) {
      schedulerTime.value = `${parts[1].padStart(2, '0')}:${parts[0].padStart(2, '0')}`
    }
  } catch (error) {
    console.error('加载通知配置失败:', error)
  }
}

// ============== 钉钉：保存 / 测试 ==============
const saveDingtalkConfig = async () => {
  savingDingtalk.value = true
  try {
    // 仅在用户实际输入了 appSecret 时才传该字段
    const payload = {
      enabled: dingtalkConfig.enabled,
      corpId: dingtalkConfig.corpId,
      agentId: dingtalkConfig.agentId,
      appKey: dingtalkConfig.appKey
    }
    if (dingtalkConfig.appSecret && dingtalkConfig.appSecret.trim()) {
      payload.appSecret = dingtalkConfig.appSecret
    }
    await updateDingtalkConfig(payload)
    ElMessage.success('钉钉配置已保存')
    dingtalkConfig.appSecret = ''
    await loadSchedulerConfig()
  } catch (error) {
    console.error('保存钉钉配置失败:', error)
  } finally {
    savingDingtalk.value = false
  }
}

const testDingtalk = async () => {
  if (!dingtalkTestTarget.value) {
    ElMessage.warning('请先填写测试接收手机号')
    return
  }
  try {
    await ElMessageBox.confirm(
      `将向手机号 ${dingtalkTestTarget.value} 真实发送一条钉钉测试消息，确认继续？`,
      '确认',
      { type: 'warning' }
    )
  } catch {
    return
  }
  testingDingtalk.value = true
  try {
    await testDingtalkChannel(dingtalkTestTarget.value)
    ElMessage.success('测试消息已发送')
  } catch (error) {
    console.error('钉钉测试失败:', error)
  } finally {
    testingDingtalk.value = false
  }
}

// ============== 邮件：保存 / 测试 ==============
const saveEmailConfig = async () => {
  savingEmail.value = true
  try {
    const payload = {
      enabled: emailConfig.enabled,
      host: emailConfig.host,
      port: emailConfig.port,
      useSsl: emailConfig.useSsl,
      user: emailConfig.user,
      fromAddr: emailConfig.fromAddr
    }
    if (emailConfig.password && emailConfig.password.trim()) {
      payload.password = emailConfig.password
    }
    await updateEmailConfig(payload)
    ElMessage.success('邮件配置已保存')
    emailConfig.password = ''
    await loadSchedulerConfig()
  } catch (error) {
    console.error('保存邮件配置失败:', error)
  } finally {
    savingEmail.value = false
  }
}

const testEmail = async () => {
  if (!emailTestTarget.value) {
    ElMessage.warning('请先填写测试收件邮箱')
    return
  }
  try {
    await ElMessageBox.confirm(
      `将向邮箱 ${emailTestTarget.value} 真实发送一封测试邮件，确认继续？`,
      '确认',
      { type: 'warning' }
    )
  } catch {
    return
  }
  testingEmail.value = true
  try {
    await testEmailChannel(emailTestTarget.value)
    ElMessage.success('测试邮件已发送')
  } catch (error) {
    console.error('邮件测试失败:', error)
  } finally {
    testingEmail.value = false
  }
}

const saveSchedulerConfig = async () => {
  savingScheduler.value = true
  try {
    await updateSchedulerConfig({
      enabled: schedulerConfig.schedulerEnabled,
      cron: schedulerConfig.schedulerCron,
      timezone: schedulerConfig.schedulerTimezone,
      lookbackWeeks: schedulerConfig.lookbackWeeks
    })
    ElMessage.success('配置已保存，调度器将在 60 秒内自动重载')
    await loadSchedulerConfig()
  } catch (error) {
    console.error('保存调度配置失败:', error)
  } finally {
    savingScheduler.value = false
  }
}

const reloadSchedulerNow = async () => {
  reloading.value = true
  try {
    await reloadScheduler()
    ElMessage.success('重载请求已记录，调度器将在 60 秒内生效')
    await loadSchedulerConfig()
  } catch (error) {
    console.error('触发重载失败:', error)
  } finally {
    reloading.value = false
  }
}

const triggerTest = async () => {
  try {
    await ElMessageBox.confirm(
      '将立即执行一次定时检查 + 通知发送。已配置的渠道会真实发出消息，请确认。',
      '确认',
      { type: 'warning' }
    )
  } catch {
    return
  }
  testing.value = true
  try {
    await triggerNotificationTest()
    ElMessage.success('已执行，请查看通知发送日志页和员工收件情况')
  } catch (error) {
    console.error('通知测试失败:', error)
  } finally {
    testing.value = false
  }
}

const handleBackup = async () => {
  backingUp.value = true
  try {
    const blob = await backupData()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const now = new Date()
    const dateStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`
    const timeStr = `${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`
    a.download = `workinghour_backup_${dateStr}_${timeStr}.db`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success('备份成功，文件已下载')
  } catch (error) {
    console.error('备份失败:', error)
    ElMessage.error('备份失败，请检查网络连接')
  } finally {
    backingUp.value = false
  }
}

const handleFileChange = (file) => {
  const isDb = file.raw.type.includes('sqlite') || file.raw.type.includes('db') || file.name.endsWith('.db')
  if (!isDb) {
    ElMessage.error('仅支持 SQLite 数据库备份文件(.db)')
    return
  }
  selectedBackupFile.value = file.raw
}

const handleRestore = () => {
  restoreDialogVisible.value = true
}

const confirmRestore = async () => {
  if (!selectedBackupFile.value) {
    ElMessage.warning('请先选择备份文件')
    return
  }

  restoring.value = true
  const formData = new FormData()
  formData.append('file', selectedBackupFile.value)

  try {
    await restoreData(formData)
    ElMessage.success('数据恢复成功，系统将重新加载')
    setTimeout(() => {
      window.location.reload()
    }, 2000)
  } catch (error) {
    console.error('恢复失败:', error)
  } finally {
    restoring.value = false
    restoreDialogVisible.value = false
    selectedBackupFile.value = null
  }
}

const handleSaveConfig = async () => {
  try {
    const configs = [
      { configKey: 'system.file_retention_days', configValue: systemConfig.fileRetentionDays.toString() },
      { configKey: 'import.max_rows', configValue: systemConfig.maxImportRows.toString() },
      { configKey: 'import.max_file_size', configValue: systemConfig.maxFileSize.toString() }
    ]
    await updateSystemConfig({ configs })
    ElMessage.success('配置保存成功')
  } catch (error) {
    console.error('保存配置失败:', error)
  }
}

const handleResetConfig = () => {
  systemConfig.fileRetentionDays = 7
  systemConfig.maxImportRows = 1000
  systemConfig.maxFileSize = 10
  ElMessage.info('配置已重置')
}

const loadConfig = async () => {
  try {
    // 一次请求获取所有配置
    const res = await getSystemConfig()
    const allConfigs = [
      ...(res.data.system || []),
      ...(res.data.import || []),
      ...(res.data.check || [])
    ]

    allConfigs.forEach(config => {
      if (config.configKey === 'system.file_retention_days') {
        systemConfig.fileRetentionDays = Number(config.configValue)
      } else if (config.configKey === 'import.max_rows') {
        systemConfig.maxImportRows = Number(config.configValue)
      } else if (config.configKey === 'import.max_file_size') {
        systemConfig.maxFileSize = Number(config.configValue)
      }
    })
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

onMounted(() => {
  // 加载系统配置
  loadConfig()
  // 加载调度配置
  loadSchedulerConfig()
  // 更新服务器时间
  setInterval(() => {
    systemInfo.serverTime = new Date().toLocaleString('zh-CN')
  }, 1000)
})
</script>

<style scoped>
.system-settings-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-card {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.backup-section {
  display: flex;
  flex-direction: column;
}

.backup-actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.backup-action {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.action-desc {
  font-size: 12px;
  color: #909399;
  margin: 0;
}

.selected-file {
  font-size: 13px;
  color: #409EFF;
  margin: 4px 0;
  word-break: break-all;
}

.config-form {
  padding: 10px 0;
}

.info-card {
  margin-bottom: 0;
}

.channel-status {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.channel-name {
  font-weight: 600;
  margin-right: 12px;
  min-width: 40px;
}

.hint-text {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}
</style>
