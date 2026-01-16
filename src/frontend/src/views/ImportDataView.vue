<template>
  <div class="import-data-view-page">
    <!-- 批次信息卡片 -->
    <el-card class="batch-info-card">
      <el-page-header @back="handleBack" :content="`导入批次号: ${batchNo}`" />
    </el-card>

    <!-- 汇总信息 -->
    <el-card v-if="summaryData" class="summary-card">
      <el-row :gutter="20">
        <el-col :span="5">
          <div class="summary-item">
            <div class="summary-label">总记录数</div>
            <div class="summary-value">{{ summaryData.totalRecords }}</div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="summary-item">
            <div class="summary-label">涉及人员数</div>
            <div class="summary-value">{{ summaryData.userCount }}</div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="summary-item">
            <div class="summary-label">涉及项目数</div>
            <div class="summary-value">{{ summaryData.projectCount }}</div>
          </div>
        </el-col>
        <el-col :span="4.5">
          <div class="summary-item">
            <div class="summary-label">总工作时长</div>
            <div class="summary-value highlight">{{ summaryData.totalWorkHours.toFixed(1) }}</div>
          </div>
        </el-col>
        <el-col :span="4.5">
          <div class="summary-item">
            <div class="summary-label">总加班时长</div>
            <div class="summary-value warning">{{ summaryData.totalOvertimeHours.toFixed(1) }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        :default-sort="{ prop: 'id', order: 'ascending' }"
        height="100%"
      >
        <el-table-column type="index" label="序号" width="60" fixed />
        <el-table-column prop="serialNo" label="Excel序号" width="100" />
        <el-table-column prop="userName" label="姓名" width="100" fixed />
        <el-table-column prop="deptName" label="部门" width="120" />
        <el-table-column prop="projectName" label="项目名称" width="200" fixed show-overflow-tooltip />
        <el-table-column prop="projectManager" label="项目经理" width="100" />
        <el-table-column prop="startTime" label="开始时间" width="120" sortable class-name="sortable-column">
          <template #default="{ row }">
            <span>{{ formatDate(row.startTime) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="endTime" label="结束时间" width="120">
          <template #default="{ row }">
            <span>{{ formatDate(row.endTime) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="workHours" label="工作时长" width="100" align="right" sortable class-name="sortable-column">
          <template #default="{ row }">
            <span>{{ row.workHours?.toFixed(1) || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="overtimeHours" label="加班时长" width="100" align="right" sortable class-name="sortable-column">
          <template #default="{ row }">
            <span>{{ row.overtimeHours?.toFixed(1) || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="workContent" label="工作内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="importTime" label="导入时间" width="160" />
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getImportDataView } from '@/api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const summaryData = ref(null)
const batchNo = ref('')

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    const res = await getImportDataView(batchNo.value, params)
    tableData.value = res.data.list || []
    summaryData.value = res.data.summary || null
    pagination.total = res.data.total || 0
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleBack = () => {
  router.push('/data/records')
}

const handleSizeChange = () => {
  loadData()
}

const handlePageChange = () => {
  loadData()
}

// 格式化日期：只显示日期部分
const formatDate = (dateTimeStr) => {
  if (!dateTimeStr) return '-'
  // ISO格式：2026-01-15T09:00:00
  return dateTimeStr.split('T')[0]
}

onMounted(() => {
  batchNo.value = route.params.batchNo || route.query.batchNo || ''
  if (batchNo.value) {
    loadData()
  } else {
    ElMessage.error('缺少批次号参数')
    router.push('/data/records')
  }
})
</script>

<style scoped>
.import-data-view-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: calc(100vh - 120px);
  overflow: hidden;
}

.batch-info-card {
  flex-shrink: 0;
  margin-bottom: 0;
}

.summary-card {
  flex-shrink: 0;
  margin-bottom: 0;
}

.summary-item {
  text-align: center;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 4px;
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

.summary-value.highlight {
  color: #409EFF;
}

.summary-value.warning {
  color: #E6A23C;
}

.table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  margin-bottom: 0;
}

.table-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
}

.pagination-wrapper {
  flex-shrink: 0;
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

:deep(.sortable-column .cell) {
  white-space: nowrap;
  overflow: visible;
}

:deep(.sortable-column .cell .caret-wrapper) {
  margin-left: 4px;
}
</style>
