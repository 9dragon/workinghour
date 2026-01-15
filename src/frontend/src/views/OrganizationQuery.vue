<template>
  <div class="organization-query-page">
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="部门名称">
          <el-select
            v-model="filterForm.deptName"
            placeholder="请选择部门"
            clearable
            filterable
            style="width: 200px"
          >
            <el-option
              v-for="item in deptList"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="姓名">
          <el-select
            v-model="filterForm.userName"
            placeholder="请选择人员"
            clearable
            filterable
            style="width: 150px"
          >
            <el-option
              v-for="item in userList"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
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
        <el-form-item label="排序">
          <el-select v-model="filterForm.sortBy" placeholder="请选择排序方式" style="width: 150px">
            <el-option label="开始时间" value="startTime" />
            <el-option label="工作时长" value="workHours" />
            <el-option label="加班时长" value="overtimeHours" />
          </el-select>
          <el-select v-model="filterForm.sortOrder" style="width: 100px; margin-left: 8px">
            <el-option label="降序" value="desc" />
            <el-option label="升序" value="asc" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleExport">
            <el-icon><Download /></el-icon>
            导出结果
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 汇总信息 -->
    <el-card v-if="summaryData" class="summary-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">涉及部门数</div>
            <div class="summary-value">{{ summaryData.deptCount }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">涉及人员数</div>
            <div class="summary-value">{{ summaryData.userCount }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">总工作时长</div>
            <div class="summary-value highlight">{{ summaryData.totalWorkHours.toFixed(1) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">总加班时长</div>
            <div class="summary-value warning">{{ summaryData.totalOvertimeHours.toFixed(1) }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        :default-sort="{ prop: 'startTime', order: 'descending' }"
        height="calc(100vh - 420px)"
      >
        <el-table-column type="index" label="序号" width="60" fixed />
        <el-table-column prop="serialNo" label="序号" width="100" />
        <el-table-column prop="deptName" label="部门" width="150" fixed />
        <el-table-column prop="userName" label="姓名" width="100" fixed />
        <el-table-column prop="startTime" label="开始时间" width="160" sortable />
        <el-table-column prop="endTime" label="结束时间" width="160" />
        <el-table-column prop="projectName" label="项目名称" width="200" show-overflow-tooltip />
        <el-table-column prop="projectManager" label="项目经理" width="100" />
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
        <el-table-column prop="createTime" label="创建时间" width="160" />
        <el-table-column prop="updateTime" label="更新时间" width="160" />
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
import { ElMessage } from 'element-plus'
import { queryByOrganization, exportQueryResult, getDataDict } from '@/api'

const loading = ref(false)
const tableData = ref([])
const summaryData = ref(null)
const deptList = ref([])
const userList = ref([])

const filterForm = reactive({
  deptName: '',
  userName: '',
  sortBy: 'startTime',
  sortOrder: 'desc'
})

const dateRange = ref([])

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const loadDict = async () => {
  try {
    const res = await getDataDict()
    deptList.value = res.data.departments || []
    userList.value = res.data.users || []
  } catch (error) {
    console.error('加载数据字典失败:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      deptName: filterForm.deptName,
      userName: filterForm.userName,
      startDate: dateRange.value?.[0],
      endDate: dateRange.value?.[1],
      sortBy: filterForm.sortBy,
      sortOrder: filterForm.sortOrder
    }
    const res = await queryByOrganization(params)
    tableData.value = res.data.list || []
    summaryData.value = res.data.summary || null
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
  filterForm.deptName = ''
  filterForm.userName = ''
  filterForm.sortBy = 'startTime'
  filterForm.sortOrder = 'desc'
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

const handleExport = async () => {
  try {
    const params = {
      dimension: 'organization',
      deptName: filterForm.deptName,
      userName: filterForm.userName,
      startDate: dateRange.value?.[0],
      endDate: dateRange.value?.[1],
      sortBy: filterForm.sortBy,
      sortOrder: filterForm.sortOrder
    }
    const res = await exportQueryResult(params)
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const now = new Date()
    const dateStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`
    a.download = `工时查询结果_组织维度_${dateStr}.xlsx`
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
  loadDict()
  loadData()
})
</script>

<style scoped>
.organization-query-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-card {
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
