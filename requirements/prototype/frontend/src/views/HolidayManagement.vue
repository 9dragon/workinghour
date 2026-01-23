<template>
  <div class="holiday-management-page">
    <!-- 工具栏 -->
    <el-card class="toolbar-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input
            v-model="searchYear"
            placeholder="按年份查询"
            type="number"
            clearable
            @change="handleSearch"
          >
            <template #prepend>年份</template>
          </el-input>
        </el-col>
        <el-col :span="7">
          <el-select
            v-model="dataSourceFilter"
            placeholder="数据来源"
            clearable
            @change="handleSearch"
            style="width: 100%"
          >
            <el-option label="全部来源" value="" />
            <el-option label="手动录入" value="manual" />
            <el-option label="API同步" value="api" />
            <el-option label="自动生成" value="auto" />
          </el-select>
        </el-col>
        <el-col :span="11" class="text-right">
          <el-button
            type="success"
            @click="showSyncDialog"
            :loading="syncing"
          >
            <el-icon><Refresh /></el-icon>
            API 同步
          </el-button>
          <el-button @click="handleGenerateWeekends">
            <el-icon><Calendar /></el-icon>
            生成周末
          </el-button>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加节假日
          </el-button>
          <el-button @click="showBatchImportDialog">
            <el-icon><Upload /></el-icon>
            批量导入
          </el-button>
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
        height="calc(100vh - 320px)"
        :default-sort="{ prop: 'holidayDate', order: 'ascending' }"
      >
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="holidayDate" label="日期" width="120" />
        <el-table-column prop="holidayName" label="节假日名称" width="150" />
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
        <el-table-column prop="createdAt" label="创建时间" width="180" />
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
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
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

        <el-alert
          title="说明"
          type="info"
          :closable="false"
          style="margin-bottom: 16px"
        >
          <p style="margin-bottom: 8px;">数据来源：timor.tech 免费节假日 API</p>
          <p style="margin-bottom: 8px;">同步后会覆盖该年份现有的 API 来源数据</p>
          <p>手动添加的数据不会被覆盖</p>
        </el-alert>
      </el-form>

      <template #footer>
        <el-button @click="syncDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSync" :loading="syncing">
          开始同步
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

    <!-- 批量导入对话框 -->
    <el-dialog
      v-model="batchImportDialogVisible"
      title="批量导入节假日"
      width="700px"
    >
      <el-alert
        title="导入格式说明"
        type="info"
        :closable="false"
        style="margin-bottom: 16px"
      >
        <p>支持JSON格式批量导入，格式如下：</p>
        <pre class="json-example">[
  {"holidayDate": "2026-01-01", "holidayName": "元旦", "isWorkday": false},
  {"holidayDate": "2026-02-10", "holidayName": "春节", "isWorkday": false}
]</pre>
      </el-alert>

      <el-input
        v-model="batchImportData"
        type="textarea"
        :rows="12"
        placeholder="请粘贴JSON格式的节假日数据"
      />

      <template #footer>
        <el-button @click="batchImportDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchImport">导入</el-button>
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
  batchImportHolidays,
  syncHolidays,
  generateWeekends
} from '@/api'

const router = useRouter()

const loading = ref(false)
const holidayList = ref([])
const searchYear = ref('')
const dataSourceFilter = ref('')
const syncing = ref(false)
const addDialogVisible = ref(false)
const batchImportDialogVisible = ref(false)
const syncDialogVisible = ref(false)
const addFormRef = ref(null)
const batchImportData = ref('')

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const addForm = reactive({
  holidayDate: '',
  holidayName: '',
  isWorkday: false
})

const syncForm = reactive({
  year: new Date().getFullYear()
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

const handleSearch = async () => {
  loading.value = true
  try {
    const params = {
      year: searchYear.value || undefined,
      dataSource: dataSourceFilter.value || undefined,
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

const showSyncDialog = () => {
  syncForm.year = new Date().getFullYear()
  syncDialogVisible.value = true
}

const handleSync = async () => {
  syncing.value = true
  try {
    const res = await syncHolidays(syncForm.year)
    ElMessage.success(`成功同步 ${syncForm.year} 年节假日 ${res.data.successCount} 条`)
    syncDialogVisible.value = false
    handleSearch()
  } catch (error) {
    ElMessage.error(error.message || '同步失败')
  } finally {
    syncing.value = false
  }
}

const handleGenerateWeekends = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要生成当前年份的周末数据吗？这将自动标记所有的周六和周日。',
      '生成确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const year = new Date().getFullYear()
    const res = await generateWeekends(year)
    ElMessage.success(`成功生成 ${year} 年周末数据 ${res.data.generatedCount} 条`)
    handleSearch()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '生成失败')
    }
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
      handleSearch()
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
    handleSearch()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const showBatchImportDialog = () => {
  batchImportData.value = ''
  batchImportDialogVisible.value = true
}

const handleBatchImport = async () => {
  if (!batchImportData.value.trim()) {
    ElMessage.warning('请输入节假日数据')
    return
  }

  try {
    const holidays = JSON.parse(batchImportData.value)

    const res = await batchImportHolidays({ holidays })

    ElMessage.success(
      `导入完成！成功 ${res.data.successCount} 条，跳过 ${res.data.skipCount} 条`
    )

    batchImportDialogVisible.value = false
    handleSearch()
  } catch (error) {
    if (error instanceof SyntaxError) {
      ElMessage.error('JSON格式错误，请检查')
    } else {
      ElMessage.error(error.message || '导入失败')
    }
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

const goBack = () => {
  router.back()
}

onMounted(() => {
  handleSearch()
})
</script>

<style scoped>
.holiday-management-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.toolbar-card {
  margin-bottom: 0;
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

.text-right {
  text-align: right;
}

.text-gray {
  color: #909399;
  margin-left: 8px;
}

.ml-2 {
  margin-left: 8px;
}

.json-example {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  margin: 8px 0;
  font-family: 'Courier New', monospace;
  overflow-x: auto;
}
</style>
