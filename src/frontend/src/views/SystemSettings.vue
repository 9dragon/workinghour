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
import { backupData, restoreData, getSystemConfig, updateSystemConfig } from '@/api'

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
      { configKey: 'system.max_import_rows', configValue: systemConfig.maxImportRows.toString() },
      { configKey: 'system.max_file_size', configValue: systemConfig.maxFileSize.toString() }
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
    const res = await getSystemConfig({ category: 'system' })
    const configs = res.data.system || []
    configs.forEach(config => {
      if (config.configKey === 'system.file_retention_days') {
        systemConfig.fileRetentionDays = Number(config.configValue)
      } else if (config.configKey === 'system.max_import_rows') {
        systemConfig.maxImportRows = Number(config.configValue)
      } else if (config.configKey === 'system.max_file_size') {
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
</style>
