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
            <p class="upload-limit">仅支持 .xlsx 或 .xls 格式，文件大小不超过 10MB</p>
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
          <el-button v-if="importResult.batchNo" @click="handleViewReport">查看导入报告</el-button>
          <el-button type="primary" @click="handleExportReport">导出报告</el-button>
        </template>
      </el-result>
    </el-card>

    <!-- 导入报告 -->
    <el-card v-if="importReport" class="report-card">
      <template #header>
        <div class="card-header">
          <el-icon><Document /></el-icon>
          <span>导入详情报告</span>
        </div>
      </template>

      <el-table :data="importReport.errors" border stripe>
        <el-table-column type="index" label="行号" width="80" align="center" />
        <el-table-column prop="field" label="字段" width="120" />
        <el-table-column prop="error" label="错误原因" />
      </el-table>
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
          <li>单次导入最多 1000 行数据</li>
          <li>文件内容需包含预设的 15 个字段，字段名称需与系统一致</li>
          <li>日期格式支持：yyyy-MM-dd HH:mm:ss 或 yyyy-MM-dd</li>
          <li>工作时长支持 1 位小数，且必须 >= 0</li>
        </ul>
      </el-alert>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { importExcel } from '@/api'

const uploadRef = ref(null)
const selectedFile = ref(null)
const duplicateStrategy = ref('skip')
const importing = ref(false)
const importResult = ref(null)
const importReport = ref(null)

const handleFileChange = (file) => {
  const isExcel = file.raw.type.includes('spreadsheet') ||
                  file.name.endsWith('.xlsx') ||
                  file.name.endsWith('.xls')
  if (!isExcel) {
    ElMessage.error('仅支持 Excel 文件格式')
    uploadRef.value?.clearFiles()
    return
  }
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB')
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

const handleViewReport = () => {
  // 打开报告详情对话框
  ElMessage.info('查看导入报告')
}

const handleExportReport = () => {
  ElMessage.info('导出报告')
}
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
