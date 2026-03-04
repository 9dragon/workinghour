<template>
  <div class="work-hour-statistics-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><DataAnalysis /></el-icon>
          <span>工时统计分析</span>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="filters">
        <el-form :inline="true" :model="filters">
          <el-form-item label="项目名称">
            <el-select v-model="filters.projectCode" placeholder="全部项目" clearable filterable style="width: 200px" @change="loadData">
              <el-option
                v-for="project in projectList"
                :key="project.projectCode"
                :label="`${project.projectCode} - ${project.projectName}`"
                :value="project.projectCode"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <!-- 汇总卡片 -->
      <el-row :gutter="20" class="summary-cards">
        <el-col :span="8">
          <el-card shadow="hover">
            <div class="summary-card">
              <div class="summary-icon" style="background: #ecf5ff; color: #409EFF">
                <el-icon :size="32"><Wallet /></el-icon>
              </div>
              <div class="summary-content">
                <div class="summary-label">预算工时（参考）</div>
                <div class="summary-value">{{ summary.totalBudgetHours }} 人天</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <div class="summary-card">
              <div class="summary-icon" style="background: #f0f9ff; color: #67C23A">
                <el-icon :size="32"><Clock /></el-icon>
              </div>
              <div class="summary-content">
                <div class="summary-label">实际工时总计</div>
                <div class="summary-value">{{ summary.totalActualHours }} 人天</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <div class="summary-card">
              <div class="summary-icon" :style="getCompletionRateIconStyle()">
                <el-icon :size="32"><TrendCharts /></el-icon>
              </div>
              <div class="summary-content">
                <div class="summary-label">预算使用率</div>
                <div class="summary-value" :style="{ color: getCompletionRateColor() }">
                  {{ summary.completionRate }}%
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 按项目统计 -->
      <div class="section">
        <h3 class="section-title">按项目统计</h3>
        <el-table :data="projectStats" border stripe style="width: 100%">
          <el-table-column prop="projectName" label="项目名称" min-width="200" fixed />
          <el-table-column label="类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getRoleTagType(row.budgetType)">
                {{ row.budgetTypeLabel }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="budgetHours" label="预算工时" width="120">
            <template #default="{ row }">
              {{ row.budgetHours }} 人天
            </template>
          </el-table-column>
          <el-table-column prop="actualHours" label="实际工时" width="120">
            <template #default="{ row }">
              {{ row.actualHours }} 人天
            </template>
          </el-table-column>
          <el-table-column label="预算使用率" width="120">
            <template #default="{ row }">
              <el-progress
                :percentage="Math.min(row.completionRate, 100)"
                :color="getProgressColor(row.completionRate)"
              />
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.completionRate)">
                {{ getStatusLabel(row.completionRate) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 按员工统计 -->
      <div class="section">
        <h3 class="section-title">按员工统计</h3>
        <el-table :data="employeeStats" border stripe style="width: 100%">
          <el-table-column prop="employeeName" label="姓名" width="120" fixed />
          <el-table-column label="类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getRoleTagType(row.role)">
                {{ row.roleLabel }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="deptName" label="部门" />
          <el-table-column prop="totalHours" label="总工时" width="120">
            <template #default="{ row }">
              {{ row.totalHours }} 人天
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getStatisticsSummary,
  getStatisticsByProject,
  getStatisticsByEmployee,
  getProjects
} from '@/api'

const CACHE_KEY = 'whs_project_filter'

const summary = reactive({
  totalBudgetHours: 0,
  totalActualHours: 0,
  completionRate: 0
})

const projectStats = ref([])
const employeeStats = ref([])
const projectList = ref([])

const filters = reactive({
  projectCode: '',
  role: ''
})

const loadData = async () => {
  try {
    // 加载汇总数据
    const summaryRes = await getStatisticsSummary({
      projectCode: filters.projectCode
    })
    Object.assign(summary, summaryRes.data)

    // 加载按项目统计
    const projectRes = await getStatisticsByProject({
      projectCode: filters.projectCode
    })
    projectStats.value = projectRes.data

    // 加载按员工统计
    const employeeRes = await getStatisticsByEmployee({
      projectCode: filters.projectCode
    })
    employeeStats.value = employeeRes.data
    // 按类型、部门、总工时排序
    const rolePriority = {
      'project_manager': 1,
      'data_collection': 2,
      'software_dev': 3,
      'staff': 4
    }
    employeeStats.value.sort((a, b) => {
      const priorityA = rolePriority[a.role] || 99
      const priorityB = rolePriority[b.role] || 99
      if (priorityA !== priorityB) {
        return priorityA - priorityB
      }
      if (a.deptName !== b.deptName) {
        return (a.deptName || '').localeCompare(b.deptName || '', 'zh-CN')
      }
      return b.totalHours - a.totalHours
    })

    // 保存筛选条件到缓存
    localStorage.setItem(CACHE_KEY, filters.projectCode || '')

  } catch (error) {
    ElMessage.error('加载统计数据失败')
    console.error(error)
  }
}

const loadProjects = async () => {
  try {
    const res = await getProjects({
      page: 1,
      size: 1000,
      projectType: 'delivery'
    })
    projectList.value = res.data.list || []
  } catch (error) {
    console.error('Failed to load projects:', error)
  }
}

const getRoleTagType = (role) => {
  const typeMap = {
    project_manager: 'success',
    data_collection: 'warning',
    software_dev: 'primary'
  }
  return typeMap[role] || 'info'
}

const getCompletionRateColor = () => {
  const rate = summary.completionRate
  if (rate < 50) return '#67C23A'
  if (rate < 80) return '#409EFF'
  if (rate <= 100) return '#E6A23C'
  return '#F56C6C'
}

const getCompletionRateIconStyle = () => {
  const rate = summary.completionRate
  if (rate < 50) return 'background: #f0f9ff; color: #67C23A'
  if (rate < 80) return 'background: #ecf5ff; color: #409EFF'
  if (rate <= 100) return 'background: #fdf6ec; color: #E6A23C'
  return 'background: #fef0f0; color: #F56C6C'
}

const getProgressColor = (rate) => {
  if (rate < 50) return '#67C23A'
  if (rate < 80) return '#409EFF'
  if (rate <= 100) return '#E6A23C'
  return '#F56C6C'
}

const getStatusType = (rate) => {
  if (rate < 50) return 'success'
  if (rate < 80) return 'primary'
  if (rate <= 100) return 'warning'
  return 'danger'
}

const getStatusLabel = (rate) => {
  if (rate < 50) return '充裕'
  if (rate < 80) return '正常'
  if (rate <= 100) return '紧张'
  return '超支'
}

onMounted(() => {
  loadProjects()

  // 从缓存恢复筛选条件
  const cachedProjectCode = localStorage.getItem(CACHE_KEY)
  if (cachedProjectCode) {
    filters.projectCode = cachedProjectCode
  }

  loadData()
})
</script>

<style scoped>
.work-hour-statistics-page {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.filters {
  margin-bottom: 20px;
}

.summary-cards {
  margin-bottom: 30px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.summary-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.summary-content {
  flex: 1;
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

.section {
  margin-top: 30px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  padding-left: 8px;
  border-left: 3px solid #409EFF;
}
</style>
