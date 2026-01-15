<template>
  <div class="import-records-page">
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="导入时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="文件名">
          <el-input
            v-model="filterForm.fileName"
            placeholder="请输入文件名"
            clearable
            style="width: 200px"
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

    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        :default-sort="{ prop: 'importTime', order: 'descending' }"
      >
        <el-table-column prop="batchNo" label="导入批次号" width="200" />
        <el-table-column prop="fileName" label="文件名" min-width="180" show-overflow-tooltip />
        <el-table-column prop="importUser" label="导入人" width="120" />
        <el-table-column prop="importTime" label="导入时间" width="160" sortable />
        <el-table-column prop="totalRows" label="总行数" width="100" align="center" />
        <el-table-column prop="successRows" label="成功" width="100" align="center">
          <template #default="{ row }">
            <span class="success-count">{{ row.successRows }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="repeatRows" label="重复" width="100" align="center">
          <template #default="{ row }">
            <span class="repeat-count">{{ row.repeatRows }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="invalidRows" label="无效" width="100" align="center">
          <template #default="{ row }">
            <span class="invalid-count">{{ row.invalidRows }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewData(row)">
              查看数据
            </el-button>
            <el-button type="primary" link size="small" @click="handleViewDetail(row)">
              查看详情
            </el-button>
            <el-button type="primary" link size="small" @click="handleDownloadReport(row)">
              下载文件
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="导入批次详情"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-descriptions v-if="currentRecord" :column="2" border>
        <el-descriptions-item label="导入批次号" :span="2">{{ currentRecord.batchNo }}</el-descriptions-item>
        <el-descriptions-item label="文件名" :span="2">{{ currentRecord.fileName }}</el-descriptions-item>
        <el-descriptions-item label="导入人">{{ currentRecord.importUser }}</el-descriptions-item>
        <el-descriptions-item label="导入时间">{{ currentRecord.importTime }}</el-descriptions-item>
        <el-descriptions-item label="总数据行数">{{ currentRecord.totalRows }}</el-descriptions-item>
        <el-descriptions-item label="成功导入">
          <span class="success-count">{{ currentRecord.successRows }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="重复数据">
          <span class="repeat-count">{{ currentRecord.repeatRows }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="无效数据">
          <span class="invalid-count">{{ currentRecord.invalidRows }}</span>
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="currentDetail && currentDetail.errors && currentDetail.errors.length > 0" style="margin-top: 20px">
        <el-divider>无效数据详情</el-divider>
        <el-table :data="currentDetail.errors" border stripe max-height="300">
          <el-table-column type="index" label="序号" width="60" align="center" />
          <el-table-column prop="row" label="行号" width="80" align="center" />
          <el-table-column prop="field" label="字段" width="120" />
          <el-table-column prop="error" label="错误原因" />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleDownloadReport(currentRecord)">
          下载文件
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getImportRecords, getImportDetail, downloadImportReport as apiDownloadReport } from '@/api'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const detailDialogVisible = ref(false)
const currentRecord = ref(null)
const currentDetail = ref(null)

const filterForm = reactive({
  fileName: ''
})

const dateRange = ref([])

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      startDate: dateRange.value?.[0],
      endDate: dateRange.value?.[1],
      fileName: filterForm.fileName
    }
    const res = await getImportRecords(params)
    tableData.value = res.data.list || []
    pagination.total = res.data.total || 0
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleQuery = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  filterForm.fileName = ''
  dateRange.value = []
  pagination.page = 1
  loadData()
}

const handleSizeChange = () => {
  loadData()
}

const handlePageChange = () => {
  loadData()
}

const handleViewDetail = async (row) => {
  currentRecord.value = row
  try {
    const res = await getImportDetail(row.batchNo)
    currentDetail.value = res.data
  } catch (error) {
    console.error('获取详情失败:', error)
  }
  detailDialogVisible.value = true
}

const handleViewData = (row) => {
  router.push({ name: 'ImportDataView', params: { batchNo: row.batchNo } })
}

const handleDownloadReport = async (row) => {
  try {
    const res = await apiDownloadReport(row.batchNo)
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = row.fileName || `导入文件_${row.batchNo}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success('文件下载成功')
  } catch (error) {
    console.error('下载文件失败:', error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.import-records-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-card {
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
</style>
