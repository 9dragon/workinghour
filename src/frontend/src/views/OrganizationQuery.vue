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
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        height="calc(100vh - 360px)"
      >
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="deptName" label="部门" width="120" />
        <el-table-column prop="userName" label="姓名" width="90" />
        <el-table-column prop="startTime" label="开始时间" width="130" />
        <el-table-column prop="endTime" label="结束时间" width="130" />
        <el-table-column prop="projectName" label="项目名称" width="150" show-overflow-tooltip />
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
        <el-table-column prop="workContent" label="工作内容" min-width="120" show-overflow-tooltip />
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
import { QuestionFilled } from '@element-plus/icons-vue'
import { queryByOrganization, getDataDict } from '@/api'

const loading = ref(false)
const tableData = ref([])
const summaryData = ref(null)
const deptList = ref([])
const userList = ref([])

const filterForm = reactive({
  deptName: '',
  userName: ''
})

const dateRange = ref([])

const pagination = reactive({
  page: 1,
  size: 10,
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
</style>
