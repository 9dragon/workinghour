<template>
  <div class="data-import-page">
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <el-icon><Upload /></el-icon>
          <span>Excel 数据导入</span>
        </div>
      </template>

      <div class="upload-section">
        <el-upload
          ref="uploadRef"
          class="upload-area"
          drag
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :on-exceed="handleExceed"
          accept=".xlsx,.xls"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">
            <p class="upload-tip">将文件拖到此处，或<em>点击上传</em></p>
            <p class="upload-limit">仅支持 .xlsx 或 .xls 格式，文件大小不超过 {{ maxFileSize }}MB</p>
          </div>
        </el-upload>

        <el-form label-width="120px" class="import-form">
          <el-form-item label="重复数据处理">
            <el-radio-group v-model="duplicateStrategy">
              <el-radio label="skip">跳过重复数据</el-radio>
              <el-radio label="overwrite">覆盖重复数据</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="importing"
              :disabled="!selectedFile"
              @click="handleImport"
            >
              开始导入
            </el-button>
            <el-button size="large" @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 导入结果 -->
    <el-card v-if="importResult" class="result-card">
      <template #header>
        <div class="card-header">
          <el-icon><CircleCheck /></el-icon>
          <span>导入结果</span>
        </div>
      </template>

      <el-result :icon="importResult.success ? 'success' : 'warning'" :title="importResult.message">
        <template #sub-title>
          <div class="result-summary">
            <el-descriptions :column="4" border>
              <el-descriptions-item label="总数据行数">{{ importResult.totalRows }}</el-descriptions-item>
              <el-descriptions-item label="成功导入">
                <span class="success-count">{{ importResult.successRows }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="重复数据">
                <span class="repeat-count">{{ importResult.repeatRows }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="无效数据">
                <span class="invalid-count">{{ importResult.invalidRows }}</span>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </template>
        <template #extra>
          <el-button v-if="importResult.batchNo" type="primary" @click="handleViewDetails">查看导入详情</el-button>
        </template>
      </el-result>
    </el-card>

    <!-- 验证错误详情 -->
    <el-card v-if="importReport?.validationErrors" class="error-card">
      <template #header>
        <div class="card-header">
          <el-icon><CircleClose /></el-icon>
          <span>部门字段验证失败</span>
        </div>
      </template>

      <el-alert
        :title="importReport.message"
        type="error"
        :closable="false"
        style="margin-bottom: 16px"
      >
        <div class="error-summary">
          共发现 <strong>{{ importReport.validationErrors.length }}</strong> 个序号的部门数据存在问题
        </div>
      </el-alert>

      <el-table :data="importReport.validationErrors" border stripe max-height="400px">
        <el-table-column prop="serialNo" label="序号" width="100" />
        <el-table-column prop="userName" label="用户" width="120" />
        <el-table-column label="行号" width="150">
          <template #default="{ row }">
            <el-tag v-for="r in row.rows" :key="r" size="small" style="margin-right: 4px">
              {{ r }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="error" label="错误说明" min-width="300" show-overflow-tooltip />
      </el-table>

      <div class="error-tips">
        <el-alert type="info" :closable="false" show-icon>
          <template #title>
            <strong>解决方法：</strong>
            <ul style="margin: 8px 0 0 0; padding-left: 20px">
              <li><strong>方法1（推荐）：</strong>在系统设置中配置用户部门信息</li>
              <li><strong>方法2：</strong>在Excel的"创建人部门"列（列45）中填写正确的部门名称</li>
              <li>配置完成后请重新上传文件</li>
            </ul>
          </template>
          <template #default>
            <div style="margin-top: 10px">
              <el-button type="primary" size="small" @click="goToUserSettings">
                <el-icon><Setting /></el-icon>
                前往配置员工部门
              </el-button>
            </div>
          </template>
        </el-alert>
      </div>
    </el-card>

    <!-- 使用说明 -->
    <el-card class="help-card">
      <template #header>
        <div class="card-header">
          <el-icon><InfoFilled /></el-icon>
          <span>导入说明</span>
        </div>
      </template>

      <el-alert title="注意事项" type="warning" :closable="false" show-icon>
        <ul class="help-list">
          <li>仅导入审批结果为"通过"且审批状态为"已完成"的记录</li>
          <li>数据唯一性标识：序号 + 姓名 + 开始时间 + 项目名称</li>
          <li>单次导入最多 {{ maxImportRows }} 行数据</li>
          <li>文件内容需包含预设的 15 个字段，字段名称需与系统一致</li>
          <li>日期格式支持：yyyy-MM-dd HH:mm:ss 或 yyyy-MM-dd</li>
          <li>工作时长支持 1 位小数，且必须 >= 0</li>
        </ul>
      </el-alert>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { importExcel, getSystemConfig } from '@/api'

const router = useRouter()

const uploadRef = ref(null)
const selectedFile = ref(null)
const duplicateStrategy = ref('skip')
const importing = ref(false)
const importResult = ref(null)
const importReport = ref(null)
const maxImportRows = ref(1000)
const maxFileSize = ref(10)

const handleFileChange = (file) => {
  const isExcel = file.raw.type.includes('spreadsheet') ||
                  file.name.endsWith('.xlsx') ||
                  file.name.endsWith('.xls')
  if (!isExcel) {
    ElMessage.error('仅支持 Excel 文件格式')
    uploadRef.value?.clearFiles()
    return
  }
  const isLtMax = file.size / 1024 / 1024 < maxFileSize.value
  if (!isLtMax) {
    ElMessage.error(`文件大小不能超过 ${maxFileSize.value}MB`)
    uploadRef.value?.clearFiles()
    return
  }
  selectedFile.value = file.raw
}

const handleExceed = () => {
  ElMessage.warning('仅支持上传一个文件，请先移除已选文件')
}

const handleImport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择要上传的文件')
    return
  }

  importing.value = true
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('strategy', duplicateStrategy.value)

  try {
    const res = await importExcel(formData)
    importResult.value = res.data
    ElMessage.success('导入完成')
    if (res.data.errors && res.data.errors.length > 0) {
      importReport.value = { errors: res.data.errors }
    }
  } catch (error) {
    console.error('导入失败:', error)
    console.error('错误响应:', error.response)

    // 处理验证错误（注意：后端将详细错误放在 error 字段中）
    if (error.response?.data?.error?.validationErrors) {
      const validationErrors = error.response.data.error.validationErrors
      const errorMsg = error.response.data.message || '部门字段验证失败'

      console.log('验证错误详情:', validationErrors)

      // 显示简化的错误提示
      ElMessage.error({
        message: `${errorMsg}，发现 ${validationErrors.length} 个序号存在问题，请查看下方详细信息`,
        duration: 5000,
        showClose: true
      })

      // 将验证错误保存到 importReport 用于展示
      importReport.value = {
        validationErrors: validationErrors,
        message: errorMsg
      }
    } else {
      console.error('其他错误:', error.response?.data)
      ElMessage.error({
        message: error.response?.data?.message || '导入失败，请检查文件格式和数据',
        duration: 5000
      })
    }
  } finally {
    importing.value = false
  }
}

const handleReset = () => {
  uploadRef.value?.clearFiles()
  selectedFile.value = null
  duplicateStrategy.value = 'skip'
  importResult.value = null
  importReport.value = null
}

const handleViewDetails = () => {
  if (!importResult.value?.batchNo) {
    ElMessage.warning('无法获取批次号')
    return
  }
  // 跳转到导入记录页面，并通过 query 参数传递批次号
  router.push({
    name: 'ImportRecords',
    query: { batchNo: importResult.value.batchNo, openDetail: 'true' }
  })
}

const handleViewReport = () => {
  // 打开报告详情对话框
  ElMessage.info('查看导入报告')
}

const handleExportReport = () => {
  ElMessage.info('导出报告')
}

const goToUserSettings = () => {
  router.push({ name: 'EmployeeManagement' })
}

const loadSystemConfig = async () => {
  try {
    const res = await getSystemConfig({ category: 'system' })
    const configs = res.data.system || []
    configs.forEach(config => {
      if (config.configKey === 'system.max_import_rows') {
        maxImportRows.value = Number(config.configValue)
      } else if (config.configKey === 'system.max_file_size') {
        maxFileSize.value = Number(config.configValue)
      }
    })
  } catch (error) {
    console.error('加载系统配置失败:', error)
  }
}

onMounted(() => {
  loadSystemConfig()
})
</script>

<style scoped>
.data-import-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.upload-card {
  min-height: 400px;
}

.upload-section {
  padding: 20px 0;
}

.upload-area {
  margin-bottom: 24px;
}

.upload-icon {
  font-size: 48px;
  color: #409EFF;
}

.upload-text {
  margin-top: 16px;
}

.upload-tip {
  font-size: 16px;
  color: #303133;
  margin: 0 0 8px 0;
}

.upload-tip em {
  color: #409EFF;
  font-style: normal;
}

.upload-limit {
  font-size: 13px;
  color: #909399;
  margin: 0;
}

.import-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-card {
  animation: fadeInUp 0.3s ease;
}

.result-summary {
  width: 100%;
  margin-top: 16px;
}

.success-count {
  color: #67C23A;
  font-weight: 600;
}

.repeat-count {
  color: #E6A23C;
  font-weight: 600;
}

.invalid-count {
  color: #F56C6C;
  font-weight: 600;
}

.report-card {
  animation: fadeInUp 0.3s ease;
  animation-delay: 0.1s;
}

.help-card {
  animation: fadeInUp 0.3s ease;
  animation-delay: 0.2s;
}

.error-card {
  animation: fadeInUp 0.3s ease;
  border: 1px solid #F56C6C;
}

.error-summary {
  margin-top: 8px;
  font-size: 14px;
}

.error-summary strong {
  color: #F56C6C;
  font-size: 16px;
}

.error-tips {
  margin-top: 16px;
}

.error-tips ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.error-tips li {
  margin-bottom: 6px;
  color: #606266;
  line-height: 1.6;
}

.help-list {
  margin: 8px 0 0 20px;
}

.help-list li {
  margin-bottom: 6px;
  color: #606266;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
