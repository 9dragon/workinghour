<template>
  <div class="holiday-management-page">
    <!-- 筛选条件卡片 -->
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="年份">
          <el-select
            v-model="filterForm.year"
            placeholder="请选择年份"
            clearable
            style="width: 150px"
          >
            <el-option
              v-for="year in availableYears"
              :key="year"
              :label="year"
              :value="year"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="调休工作日">
          <el-select
            v-model="filterForm.isWorkday"
            placeholder="全部"
            clearable
            style="width: 120px"
          >
            <el-option label="是" :value="true" />
            <el-option label="否" :value="false" />
          </el-select>
        </el-form-item>

        <el-form-item label="周末">
          <el-select
            v-model="filterForm.isWeekend"
            placeholder="全部"
            clearable
            style="width: 120px"
          >
            <el-option label="是" :value="true" />
            <el-option label="否" :value="false" />
          </el-select>
        </el-form-item>

        <el-form-item label="数据来源">
          <el-select
            v-model="filterForm.dataSource"
            placeholder="全部来源"
            clearable
            style="width: 130px"
          >
            <el-option label="手动录入" value="manual" />
            <el-option label="API同步" value="api" />
            <el-option label="自动生成" value="auto" />
          </el-select>
        </el-form-item>

        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 260px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleQuery">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 工具栏卡片 -->
    <el-card class="toolbar-card">
      <el-row :gutter="20">
        <el-col :span="24" class="toolbar-actions">
          <div class="button-group">
            <el-button type="success" @click="showSyncDialog" :loading="syncing">
              <el-icon><Refresh /></el-icon>
              API 同步
            </el-button>

            <el-button type="warning" @click="showGenerateWeekendsDialog">
              <el-icon><Calendar /></el-icon>
              生成周末
            </el-button>

            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              添加节假日
            </el-button>

            <el-button type="danger" @click="handleClearAll" plain>
              <el-icon><Delete /></el-icon>
              清空全部
            </el-button>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 统计卡片 -->
    <el-card class="summary-card" v-loading="summaryLoading">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">节假日总数</div>
            <div class="summary-value">{{ summaryData.total }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">法定节假日</div>
            <div class="summary-value normal">{{ summaryData.legal }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">调休工作日</div>
            <div class="summary-value warning">{{ summaryData.workdays }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">周末</div>
            <div class="summary-value info">{{ summaryData.weekends }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 节假日列表表格 -->
    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="holidayList"
        border
        stripe
        height="calc(100vh - 380px)"
        :default-sort="{ prop: 'holidayDate', order: 'ascending' }"
        :cell-style="{ 'white-space': 'nowrap' }"
      >
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="holidayDate" label="日期" width="120" />
        <el-table-column prop="holidayName" label="节假日名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="year" label="年份" width="100" align="center" />
        <el-table-column prop="isWeekend" label="周末" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.isWeekend" type="info" size="small">是</el-tag>
            <span v-else style="color: #909399">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="isWorkday" label="调休工作日" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.isWorkday ? 'warning' : 'success'" size="small">
              {{ row.isWorkday ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="dataSource" label="数据来源" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getDataSourceType(row.dataSource)" size="small">
              {{ getDataSourceLabel(row.dataSource) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="160" align="center">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              link
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleQuery"
          @current-change="handleQuery"
        />
      </div>
    </el-card>

    <!-- API同步对话框 -->
    <el-dialog
      v-model="syncDialogVisible"
      title="从第三方 API 同步节假日"
      width="500px"
    >
      <el-form :model="syncForm" label-width="100px">
        <el-form-item label="选择年份">
          <el-select v-model="syncForm.year" placeholder="请选择年份" style="width: 100%">
            <el-option
              v-for="year in availableYears"
              :key="year"
              :label="year"
              :value="year"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="处理方式">
          <el-radio-group v-model="syncForm.mode">
            <el-radio label="skip">跳过已存在数据</el-radio>
            <el-radio label="overwrite">覆盖已存在数据</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-alert
          title="说明"
          type="info"
          :closable="false"
          style="margin-bottom: 16px"
        >
          <p style="margin-bottom: 8px;">数据来源：timor.tech 免费节假日 API</p>
          <p style="margin-bottom: 8px;">跳过模式：保留所有已存在的数据</p>
          <p>覆盖模式：仅覆盖API来源的数据，保留手动添加的数据</p>
        </el-alert>
      </el-form>

      <template #footer>
        <el-button @click="syncDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSync" :loading="syncing">
          开始同步
        </el-button>
      </template>
    </el-dialog>

    <!-- 生成周末对话框 -->
    <el-dialog
      v-model="generateWeekendsDialogVisible"
      title="生成周末数据"
      width="500px"
    >
      <el-form :model="generateWeekendsForm" label-width="100px">
        <el-form-item label="选择年份">
          <el-select v-model="generateWeekendsForm.year" placeholder="请选择年份" style="width: 100%">
            <el-option
              v-for="year in availableYears"
              :key="year"
              :label="year"
              :value="year"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="处理方式">
          <el-radio-group v-model="generateWeekendsForm.mode">
            <el-radio label="skip">跳过已存在数据</el-radio>
            <el-radio label="overwrite">覆盖已存在数据</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-alert
          title="说明"
          type="info"
          :closable="false"
          style="margin-bottom: 16px"
        >
          <p style="margin-bottom: 8px;">将自动标记该年份的所有周六和周日</p>
          <p style="margin-bottom: 8px;">跳过模式：保留所有已存在的数据</p>
          <p>覆盖模式：仅覆盖自动生成的周末数据</p>
        </el-alert>
      </el-form>

      <template #footer>
        <el-button @click="generateWeekendsDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleGenerateWeekends" :loading="generating">
          开始生成
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加节假日对话框 -->
    <el-dialog
      v-model="addDialogVisible"
      title="添加节假日"
      width="500px"
    >
      <el-form :model="addForm" :rules="addRules" ref="addFormRef" label-width="120px">
        <el-form-item label="日期" prop="holidayDate">
          <el-date-picker
            v-model="addForm.holidayDate"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="节假日名称" prop="holidayName">
          <el-input v-model="addForm.holidayName" placeholder="如：元旦、春节" />
        </el-form-item>
        <el-form-item label="调休工作日" prop="isWorkday">
          <el-switch v-model="addForm.isWorkday" />
          <span class="ml-2 text-gray">
            {{ addForm.isWorkday ? '是（需要上班的周末）' : '否（法定节假日）' }}
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAdd">确定</el-button>
      </template>
    </el-dialog>

    <!-- 清空确认对话框 -->
    <el-dialog
      v-model="clearAllDialogVisible"
      title="清空确认"
      width="450px"
    >
      <el-alert
        title="警告"
        type="error"
        :closable="false"
        style="margin-bottom: 16px"
      >
        <p style="margin-bottom: 8px;">此操作将<strong style="color: #f56c6c;">删除所有节假日数据</strong>！</p>
        <p style="margin-bottom: 8px;">包括手动录入、API同步和自动生成的所有记录</p>
        <p>此操作不可撤销，请谨慎操作！</p>
      </el-alert>

      <el-form label-width="100px">
        <el-form-item label="确认文本">
          <el-input
            v-model="clearConfirmText"
            placeholder="请输入 'DELETE ALL' 以确认"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="clearAllDialogVisible = false">取消</el-button>
        <el-button
          type="danger"
          @click="confirmClearAll"
          :disabled="clearConfirmText !== 'DELETE ALL'"
          :loading="clearing"
        >
          确认清空
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getHolidays,
  addHoliday,
  deleteHoliday,
  syncHolidays,
  generateWeekends,
  clearAllHolidays,
  getHolidaySummary
} from '@/api'

const router = useRouter()

const loading = ref(false)
const holidayList = ref([])
const syncing = ref(false)
const generating = ref(false)
const clearing = ref(false)
const summaryLoading = ref(false)
const addDialogVisible = ref(false)
const syncDialogVisible = ref(false)
const generateWeekendsDialogVisible = ref(false)
const clearAllDialogVisible = ref(false)
const addFormRef = ref(null)
const clearConfirmText = ref('')
const dateRange = ref([])

const summaryData = reactive({
  total: 0,
  legal: 0,
  workdays: 0,
  weekends: 0
})

const filterForm = reactive({
  year: null,
  isWorkday: null,
  isWeekend: null,
  dataSource: ''
})

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const addForm = reactive({
  holidayDate: '',
  holidayName: '',
  isWorkday: false
})

const syncForm = reactive({
  year: new Date().getFullYear(),
  mode: 'skip'
})

const generateWeekendsForm = reactive({
  year: new Date().getFullYear(),
  mode: 'skip'
})

const addRules = {
  holidayDate: [
    { required: true, message: '请选择日期', trigger: 'change' }
  ],
  holidayName: [
    { required: true, message: '请输入节假日名称', trigger: 'blur' }
  ]
}

// 可选年份列表（当前年前后5年）
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 11 }, (_, i) => currentYear - 5 + i)
})

// 查询按钮点击
const handleQuery = () => {
  pagination.page = 1
  loadHolidays()
  loadSummary()
}

// 重置按钮点击
const handleReset = () => {
  filterForm.year = null
  filterForm.isWorkday = null
  filterForm.isWeekend = null
  filterForm.dataSource = ''
  dateRange.value = []
  pagination.page = 1
  loadHolidays()
  loadSummary()
}

// 加载数据
const loadHolidays = async () => {
  loading.value = true
  try {
    const params = {
      year: filterForm.year || undefined,
      isWorkday: filterForm.isWorkday ?? undefined,
      isWeekend: filterForm.isWeekend ?? undefined,
      dataSource: filterForm.dataSource || undefined,
      startDate: dateRange.value?.[0] || undefined,
      endDate: dateRange.value?.[1] || undefined,
      page: pagination.page,
      size: pagination.size
    }

    const res = await getHolidays(params)
    holidayList.value = res.data.list || []
    pagination.total = res.data.total || 0
  } catch (error) {
    ElMessage.error(error.message || '查询失败')
  } finally {
    loading.value = false
  }
}

// 加载统计数据
const loadSummary = async () => {
  summaryLoading.value = true
  try {
    const params = {
      year: filterForm.year || undefined
    }
    const res = await getHolidaySummary(params)
    Object.assign(summaryData, res.data)
  } catch (error) {
    console.error('加载统计数据失败:', error)
  } finally {
    summaryLoading.value = false
  }
}

const showSyncDialog = () => {
  syncForm.year = new Date().getFullYear()
  syncForm.mode = 'skip'
  syncDialogVisible.value = true
}

const handleSync = async () => {
  if (!syncForm.year) {
    ElMessage.warning('请选择年份')
    return
  }

  syncing.value = true
  try {
    const res = await syncHolidays(syncForm.year, syncForm.mode)
    ElMessage.success(`成功同步 ${syncForm.year} 年节假日 ${res.data.successCount} 条`)
    syncDialogVisible.value = false
    loadHolidays()
    loadSummary()
  } catch (error) {
    ElMessage.error(error.message || '同步失败')
  } finally {
    syncing.value = false
  }
}

const showGenerateWeekendsDialog = () => {
  generateWeekendsForm.year = new Date().getFullYear()
  generateWeekendsForm.mode = 'skip'
  generateWeekendsDialogVisible.value = true
}

const handleGenerateWeekends = async () => {
  if (!generateWeekendsForm.year) {
    ElMessage.warning('请选择年份')
    return
  }

  generating.value = true
  try {
    const res = await generateWeekends(generateWeekendsForm.year, generateWeekendsForm.mode)
    ElMessage.success(
      `成功生成 ${generateWeekendsForm.year} 年周末数据 ${res.data.generatedCount} 条`
    )
    generateWeekendsDialogVisible.value = false
    loadHolidays()
    loadSummary()
  } catch (error) {
    ElMessage.error(error.message || '生成失败')
  } finally {
    generating.value = false
  }
}

const showAddDialog = () => {
  addForm.holidayDate = ''
  addForm.holidayName = ''
  addForm.isWorkday = false
  addDialogVisible.value = true
}

const handleAdd = async () => {
  if (!addFormRef.value) return

  await addFormRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      await addHoliday({
        holidayDate: addForm.holidayDate,
        holidayName: addForm.holidayName,
        isWorkday: addForm.isWorkday ? 1 : 0
      })

      ElMessage.success('添加成功')
      addDialogVisible.value = false
      loadHolidays()
      loadSummary()
    } catch (error) {
      ElMessage.error(error.message || '添加失败')
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 "${row.holidayName} (${row.holidayDate})" 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteHoliday(row.id)
    ElMessage.success('删除成功')
    loadHolidays()
    loadSummary()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const handleClearAll = () => {
  clearConfirmText.value = ''
  clearAllDialogVisible.value = true
}

const confirmClearAll = async () => {
  if (clearConfirmText.value !== 'DELETE ALL') {
    ElMessage.warning('请输入 DELETE ALL 以确认')
    return
  }

  clearing.value = true
  try {
    await clearAllHolidays()
    ElMessage.success('已清空所有节假日数据')
    clearAllDialogVisible.value = false
    filterForm.year = null
    filterForm.isWorkday = null
    filterForm.isWeekend = null
    filterForm.dataSource = ''
    dateRange.value = []
    pagination.page = 1
    loadHolidays()
    loadSummary()
  } catch (error) {
    ElMessage.error(error.message || '清空失败')
  } finally {
    clearing.value = false
  }
}

const getDataSourceLabel = (source) => {
  const labels = {
    'manual': '手动',
    'api': 'API',
    'auto': '自动'
  }
  return labels[source] || source
}

const getDataSourceType = (source) => {
  const types = {
    'manual': 'primary',
    'api': 'success',
    'auto': 'info'
  }
  return types[source] || ''
}

const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return '-'
  const date = new Date(dateTimeStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  loadHolidays()
  loadSummary()
})
</script>

<style scoped>
.holiday-management-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-card {
  margin-bottom: 0;
}

.filter-card :deep(.el-card__body) {
  padding: 20px 24px;
}

.toolbar-card {
  margin-bottom: 0;
}

.summary-card {
  margin-bottom: 0;
}

.summary-item {
  text-align: center;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 4px;
  transition: all 0.3s;
}

.summary-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.summary-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.summary-value.normal {
  color: #67C23A;
}

.summary-value.warning {
  color: #E6A23C;
}

.summary-value.info {
  color: #409EFF;
}

.summary-value.primary {
  color: #409EFF;
}

.summary-value.success {
  color: #67C23A;
}

.table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.table-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.toolbar-actions {
  display: flex;
  justify-content: flex-end;
}

.button-group {
  display: flex;
  gap: 10px;
  flex-wrap: nowrap;
}

.text-gray {
  color: #909399;
  margin-left: 8px;
}

.ml-2 {
  margin-left: 8px;
}
</style>
