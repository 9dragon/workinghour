<template>
  <div class="import-data-view-page">
    <!-- 批次信息卡片 -->
    <el-card class="batch-info-card">
      <el-page-header @back="handleBack" :content="`导入批次号: ${batchNo}`">
        <template #extra>
          <el-button type="success" @click="handleExport">
            <el-icon><Download /></el-icon>
            导出数据
          </el-button>
        </template>
      </el-page-header>
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
        :default-sort="{ prop: 'startTime', order: 'descending' }"
        height="calc(100vh - 380px)"
      >
        <el-table-column type="index" label="序号" width="60" fixed />
        <el-table-column prop="serialNo" label="序号" width="100" />
        <el-table-column prop="userName" label="姓名" width="100" fixed />
        <el-table-column prop="deptName" label="部门" width="120" />
        <el-table-column prop="projectName" label="项目名称" width="200" fixed show-overflow-tooltip />
        <el-table-column prop="projectManager" label="项目经理" width="100" />
        <el-table-column prop="startTime" label="开始时间" width="160" sortable />
        <el-table-column prop="endTime" label="结束时间" width="160" />
        <el-table-column prop="workHours" label="工作时长" width="100" align="right" sortable>
          <template #default="{ row }">
            <span>{{ row.workHours?.toFixed(1) || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="overtimeHours" label="加班时长" width="100" align="right" sortable>
          <template #default="{ row }">
            <span>{{ row.overtimeHours?.toFixed(1) || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="workContent" label="工作内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="approvalResult" label="审批结果" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.approvalResult === '通过'" type="success" size="small">通过</el-tag>
            <el-tag v-else type="danger" size="small">{{ row.approvalResult || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="approvalStatus" label="审批状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.approvalStatus === '已完成'" type="success" size="small">已完成</el-tag>
            <el-tag v-else type="info" size="small">{{ row.approvalStatus || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="160" />
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getImportDataView, exportImportData } from '@/api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const summaryData = ref(null)
const batchNo = ref('')

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

const handleExport = async () => {
  try {
    const res = await exportImportData(batchNo.value)
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `工时导入数据_${batchNo.value}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
  }
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
}

.batch-info-card {
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
</style>
