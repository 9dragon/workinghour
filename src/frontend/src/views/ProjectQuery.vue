<template>
  <div class="project-query-page">
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="项目经理">
          <el-select
            v-model="filterForm.projectManager"
            placeholder="请选择项目经理"
            clearable
            filterable
            @change="handleManagerChange"
            style="width: 150px"
          >
            <el-option
              v-for="item in managerList"
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
            @change="handleProjectChange"
            style="width: 200px"
          >
            <el-option
              v-for="item in filteredProjectList"
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
            <div class="summary-label">涉及项目数</div>
            <div class="summary-value">{{ summaryData.projectCount }}</div>
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
        :row-style="{ height: '50px' }"
        :cell-style="{ 'white-space': 'nowrap', padding: '8px 0' }"
        height="calc(100vh - 360px)"
      >
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="userName" label="姓名" width="90" />
        <el-table-column prop="deptName" label="部门" width="130" />
        <el-table-column prop="projectName" label="项目名称" width="200" show-overflow-tooltip />
        <el-table-column prop="projectManager" label="项目经理" width="90" show-overflow-tooltip />
        <el-table-column prop="startTime" label="开始时间" width="145" />
        <el-table-column prop="endTime" label="结束时间" width="145" />
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
import { ref, reactive, onMounted, computed } from 'vue'
import { QuestionFilled } from '@element-plus/icons-vue'
import { queryByProject, getDataDict } from '@/api'

const loading = ref(false)
const tableData = ref([])
const summaryData = ref(null)
const projectList = ref([])
const managerList = ref([])

// 映射关系
const projectManagerMap = ref({})  // 项目 -> 经理列表
const managerProjectMap = ref({})  // 经理 -> 项目列表

const filterForm = reactive({
  projectName: '',
  projectManager: ''
})

const dateRange = ref([])

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

// 计算过滤后的项目列表
const filteredProjectList = computed(() => {
  if (!filterForm.projectManager) {
    return projectList.value
  }
  return managerProjectMap.value[filterForm.projectManager] || []
})

const loadDict = async () => {
  try {
    const res = await getDataDict()
    projectList.value = res.data.projects || []
    managerList.value = res.data.managers || []
    projectManagerMap.value = res.data.projectManagerMap || {}
    managerProjectMap.value = res.data.managerProjectMap || {}
  } catch (error) {
    console.error('加载数据字典失败:', error)
  }
}

// 项目经理改变时，清空项目名称
const handleManagerChange = () => {
  filterForm.projectName = ''
}

// 项目名称改变时，清空项目经理
const handleProjectChange = () => {
  filterForm.projectManager = ''
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      projectName: filterForm.projectName,
      projectManager: filterForm.projectManager,
      startDate: dateRange.value?.[0],
      endDate: dateRange.value?.[1]
    }
    const res = await queryByProject(params)
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
  filterForm.projectName = ''
  filterForm.projectManager = ''
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
.project-query-page {
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

/* 确保表格单元格不换行 */
:deep(.el-table__cell) {
  overflow: hidden;
  text-overflow: ellipsis;
}

:deep(.el-table .cell) {
  white-space: nowrap;
  word-break: keep-all;
}
</style>
