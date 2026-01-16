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
        <el-table-column prop="importTime" label="导入时间" width="160" sortable class-name="sortable-column" />
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
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewData(row)">
              查看数据
            </el-button>
            <el-button type="primary" link size="small" @click="handleViewDetail(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
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

      <!-- 无效数据详情 -->
      <div v-if="currentDetail && currentDetail.errors && currentDetail.errors.length > 0" style="margin-top: 20px">
        <el-divider>无效数据详情（共 {{ currentDetail.errors.length }} 条）</el-divider>

        <el-alert
          type="info"
          :closable="false"
          style="margin-bottom: 12px"
        >
          以下为导入失败的数据详情，请根据行号和错误原因修改Excel文件后重新导入
        </el-alert>

        <el-table
          :data="paginatedErrors"
          border
          stripe
          max-height="400"
          :default-sort="{ prop: 'row', order: 'ascending' }"
        >
          <el-table-column type="index" label="序号" width="60" align="center" />
          <el-table-column prop="row" label="Excel行号" width="100" align="center" sortable>
            <template #default="{ row }">
              <el-tag type="warning">{{ row.row }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="field" label="错误字段" width="180">
            <template #default="{ row }">
              <el-tag size="small" type="danger">{{ row.field }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="error" label="错误原因" min-width="300" show-overflow-tooltip>
            <template #default="{ row }">
              <span style="color: #F56C6C">{{ row.error }}</span>
            </template>
          </el-table-column>
        </el-table>

        <div class="error-pagination-wrapper">
          <el-pagination
            v-model:current-page="errorPagination.page"
            v-model:page-size="errorPagination.size"
            :page-sizes="[10, 20, 50, 100, 200]"
            :total="currentDetail.errors.length"
            layout="total, sizes, prev, pager, next, jumper"
            small
          />
        </div>
      </div>

      <!-- 重复数据详情 -->
      <div v-if="currentDetail && currentDetail.repeats && currentDetail.repeats.length > 0" style="margin-top: 20px">
        <el-divider>重复数据详情（共 {{ currentDetail.repeats.length }} 条）</el-divider>

        <el-alert
          type="warning"
          :closable="false"
          style="margin-bottom: 12px"
        >
          以下为导入时检测到的重复数据，根据您选择的重复数据处理策略已进行处理
        </el-alert>

        <el-table
          :data="paginatedRepeats"
          border
          stripe
          max-height="400"
          :default-sort="{ prop: 'row', order: 'ascending' }"
        >
          <el-table-column type="index" label="序号" width="60" align="center" />
          <el-table-column prop="row" label="Excel行号" width="100" align="center" sortable>
            <template #default="{ row }">
              <el-tag type="warning">{{ row.row }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="field" label="类型" width="120">
            <template #default="{ row }">
              <el-tag size="small" type="warning">{{ row.field }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="error" label="重复数据说明" min-width="280" show-overflow-tooltip>
            <template #default="{ row }">
              <span style="color: #E6A23C">{{ row.error }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="existing_batch" label="原批次号" width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <el-tag size="small" type="info">{{ row.existing_batch }}</el-tag>
            </template>
          </el-table-column>
        </el-table>

        <div class="error-pagination-wrapper">
          <el-pagination
            v-model:current-page="repeatPagination.page"
            v-model:page-size="repeatPagination.size"
            :page-sizes="[10, 20, 50, 100, 200]"
            :total="currentDetail.repeats.length"
            layout="total, sizes, prev, pager, next, jumper"
            small
          />
        </div>
      </div>

      <div v-if="(!currentDetail?.errors || currentDetail.errors.length === 0) && (!currentDetail?.repeats || currentDetail.repeats.length === 0)" style="margin-top: 20px">
        <el-empty description="暂无错误或重复数据" :image-size="100" />
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getImportRecords, getImportDetail } from '@/api'

const router = useRouter()
const route = useRoute()

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
  size: 10,
  total: 0
})

// 错误详情分页
const errorPagination = reactive({
  page: 1,
  size: 10
})

// 重复数据详情分页
const repeatPagination = reactive({
  page: 1,
  size: 10
})

// 计算当前页显示的错误数据
const paginatedErrors = computed(() => {
  if (!currentDetail.value || !currentDetail.value.errors) {
    return []
  }
  const start = (errorPagination.page - 1) * errorPagination.size
  const end = start + errorPagination.size
  return currentDetail.value.errors.slice(start, end)
})

// 计算当前页显示的重复数据
const paginatedRepeats = computed(() => {
  if (!currentDetail.value || !currentDetail.value.repeats) {
    return []
  }
  const start = (repeatPagination.page - 1) * repeatPagination.size
  const end = start + repeatPagination.size
  return currentDetail.value.repeats.slice(start, end)
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
  // 重置错误分页和重复数据分页
  errorPagination.page = 1
  errorPagination.size = 10
  repeatPagination.page = 1
  repeatPagination.size = 10
  try {
    const res = await getImportDetail(row.batchNo)
    console.log('导入详情响应:', res)
    console.log('响应数据:', res.data)
    console.log('错误详情:', res.data?.errors)
    console.log('错误数量:', res.data?.errors?.length)
    console.log('重复数据详情:', res.data?.repeats)
    console.log('重复数据数量:', res.data?.repeats?.length)
    currentDetail.value = res.data
  } catch (error) {
    console.error('获取详情失败:', error)
  }
  detailDialogVisible.value = true
}

const handleViewData = (row) => {
  router.push({ name: 'ImportDataView', params: { batchNo: row.batchNo } })
}

onMounted(async () => {
  await loadData()
  // 检查是否需要自动打开详情对话框
  const { batchNo, openDetail } = route.query
  if (batchNo && openDetail === 'true') {
    // 查找对应的记录
    const record = tableData.value.find(item => item.batchNo === batchNo)
    if (record) {
      handleViewDetail(record)
    } else {
      // 如果当前页没有找到，可能需要查询其他页或直接通过批次号打开
      currentRecord.value = { batchNo }
      errorPagination.page = 1
      errorPagination.size = 10
      repeatPagination.page = 1
      repeatPagination.size = 10
      try {
        const res = await getImportDetail(batchNo)
        currentDetail.value = res.data
        detailDialogVisible.value = true
      } catch (error) {
        console.error('获取详情失败:', error)
        ElMessage.error('无法找到该导入记录')
      }
    }
  }
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

.error-pagination-wrapper {
  margin-top: 12px;
  display: flex;
  justify-content: center;
  padding-top: 12px;
  border-top: 1px solid #EBEEF5;
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

:deep(.sortable-column .cell) {
  white-space: nowrap;
  overflow: visible;
}

:deep(.sortable-column .cell .caret-wrapper) {
  margin-left: 4px;
}
</style>
