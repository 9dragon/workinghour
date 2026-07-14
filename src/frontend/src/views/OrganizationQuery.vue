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
        <el-form-item label="项目名称">
          <el-select
            v-model="filterForm.projectName"
            placeholder="请选择项目"
            clearable
            filterable
            style="width: 200px"
          >
            <el-option
              v-for="item in projectList"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <template #label>
            <span>时间范围</span>
            <el-tooltip
              effect="dark"
              placement="bottom"
            >
              <template #content>
                <div style="line-height: 1.8;">
                  <div style="font-weight: 600; margin-bottom: 4px;">⚠️ 时间范围筛选说明</div>
                  <div>仅显示<strong>开始时间和结束时间</strong>都在时间范围内的工时记录</div>
                  <div style="margin-top: 8px; color: #ffd700;">请确保筛选时间范围与工时报工范围相匹配</div>
                </div>
              </template>
              <el-icon style="margin-left: 4px; cursor: help; color: #409EFF; vertical-align: middle;">
                <QuestionFilled />
              </el-icon>
            </el-tooltip>
          </template>
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
            <div class="summary-label">总工作人天</div>
            <div class="summary-value highlight">{{ ((summaryData.totalWorkHours || 0) / 8).toFixed(1) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">总加班人天</div>
            <div class="summary-value warning">{{ ((summaryData.totalOvertimeHours || 0) / 8).toFixed(1) }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="table-card">
      <div class="table-toolbar">
        <el-button
          type="danger"
          :disabled="selectedRows.length === 0"
          @click="handleBatchDelete"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
        <span v-if="selectedRows.length" class="selection-info">
          已选 {{ selectedRows.length }} 条
        </span>
      </div>
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        height="calc(100vh - 360px)"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="deptName" label="部门" width="120" />
        <el-table-column prop="userName" label="姓名" width="90" />
        <el-table-column prop="startTime" label="开始时间" width="130" />
        <el-table-column prop="endTime" label="结束时间" width="130" />
        <el-table-column prop="projectName" label="项目名称" width="380" show-overflow-tooltip />
        <el-table-column prop="projectManager" label="项目经理" width="90" />
        <el-table-column prop="workHours" label="工作时长" width="90" align="right">
          <template #default="{ row }">
            <span>{{ row.workHours?.toFixed(1) || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="overtimeHours" label="加班时长" width="90" align="right">
          <template #default="{ row }">
            <span>{{ row.overtimeHours?.toFixed(1) || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="workContent" label="工作内容" min-width="80" show-overflow-tooltip />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" link size="small" @click="handleDelete(row)">
              删除
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { QuestionFilled, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { queryByOrganization, getDataDict, deleteWorkHour, batchDeleteWorkHours } from '@/api'

const loading = ref(false)
const tableData = ref([])
const summaryData = ref(null)
const deptList = ref([])
const userList = ref([])
const projectList = ref([])

const filterForm = reactive({
  deptName: '',
  userName: '',
  projectName: ''
})

const dateRange = ref([])

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const selectedRows = ref([])

const loadDict = async () => {
  try {
    const res = await getDataDict()
    deptList.value = res.data.departments || []
    userList.value = res.data.users || []
    projectList.value = res.data.workProjects || []
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
      projectName: filterForm.projectName,
      startDate: dateRange.value?.[0],
      endDate: dateRange.value?.[1]
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
  filterForm.projectName = ''
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

const handleSelectionChange = (val) => {
  selectedRows.value = val
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除 ${row.userName} 的该条工时记录吗？此操作不可恢复。`,
    '删除确认',
    { type: 'warning' }
  )
    .then(async () => {
      try {
        await deleteWorkHour(row.id)
        ElMessage.success('删除成功')
        if (tableData.value.length === 1 && pagination.page > 1) {
          pagination.page -= 1
        }
        await loadData()
      } catch (error) {
        ElMessage.error(error.response?.data?.message || '删除失败')
        console.error(error)
      }
    })
    .catch(() => {})
}

const handleBatchDelete = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要删除的记录')
    return
  }
  const count = selectedRows.value.length
  ElMessageBox.confirm(
    `确定要删除选中的 ${count} 条工时记录吗？此操作不可恢复。`,
    '批量删除确认',
    { type: 'warning' }
  )
    .then(async () => {
      try {
        await batchDeleteWorkHours(selectedRows.value.map(r => r.id))
        ElMessage.success(`成功删除 ${count} 条记录`)
        selectedRows.value = []
        if (tableData.value.length === count && pagination.page > 1) {
          pagination.page -= 1
        }
        await loadData()
      } catch (error) {
        ElMessage.error(error.response?.data?.message || '删除失败')
        console.error(error)
      }
    })
    .catch(() => {})
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
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.summary-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.summary-value {
  font-size: 20px;
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

.table-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.selection-info {
  font-size: 13px;
  color: #606266;
}
</style>
