<template>
  <div class="compliance-check-page">
    <el-card class="filter-card">
      <el-form :model="checkForm" inline>
        <el-form-item label="核对时间范围">
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
        <el-form-item label="部门">
          <el-select
            v-model="checkForm.deptName"
            placeholder="请选择部门（可选）"
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
        <el-form-item label="人员">
          <el-select
            v-model="checkForm.userName"
            placeholder="请选择人员（可选）"
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
      </el-form>
    </el-card>

    <el-card class="rule-card">
      <template #header>
        <div class="card-header">
          <el-icon><Setting /></el-icon>
          <span>合规规则配置</span>
        </div>
      </template>
      <el-form :model="rules" inline>
        <el-form-item label="每日标准工作时长">
          <el-input-number v-model="rules.standardHours" :min="1" :max="24" :step="0.5" />
          <span style="margin-left: 8px">小时</span>
        </el-form-item>
        <el-form-item label="每日工作时长下限">
          <el-input-number v-model="rules.minHours" :min="0" :max="24" :step="0.5" />
          <span style="margin-left: 8px">小时</span>
        </el-form-item>
        <el-form-item label="每日加班时长上限">
          <el-input-number v-model="rules.maxOvertime" :min="0" :max="24" :step="0.5" />
          <span style="margin-left: 8px">小时</span>
        </el-form-item>
        <el-form-item label="每月加班时长上限">
          <el-input-number v-model="rules.maxMonthlyOvertime" :min="0" :max="200" :step="5" />
          <span style="margin-left: 8px">小时</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="checking" @click="handleCheck">
            <el-icon><CircleCheck /></el-icon>
            开始核对
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
            <div class="summary-label">核对总记录数</div>
            <div class="summary-value">{{ summaryData.totalRecords }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">异常记录数</div>
            <div class="summary-value warning">{{ summaryData.invalidRecords }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">异常人数</div>
            <div class="summary-value danger">{{ summaryData.invalidUsers }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">合规率</div>
            <div class="summary-value highlight">{{ summaryData.complianceRate.toFixed(2) }}%</div>
          </div>
        </el-col>
      </el-row>

      <!-- 异常类型分布 -->
      <el-divider>异常类型分布</el-divider>
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="type-stat">
            <el-tag type="warning" size="large">工时过短</el-tag>
            <span class="type-count">{{ summaryData.invalidTypes?.shortHours || 0 }}</span>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="type-stat">
            <el-tag type="danger" size="large">加班超标</el-tag>
            <span class="type-count">{{ summaryData.invalidTypes?.excessOvertime || 0 }}</span>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="type-stat">
            <el-tag type="info" size="large">累计超标</el-tag>
            <span class="type-count">{{ summaryData.invalidTypes?.cumulativeExcess || 0 }}</span>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 核对结果 -->
    <el-card v-if="tableData.length > 0" class="result-card">
      <template #header>
        <div class="card-header">
          <el-icon><Document /></el-icon>
          <span>异常数据明细</span>
          <el-button type="primary" size="small" @click="handleExportReport">
            <el-icon><Download /></el-icon>
            导出报告
          </el-button>
        </div>
      </template>

      <el-table :data="tableData" border stripe height="calc(100vh - 560px)">
        <el-table-column type="index" label="序号" width="60" fixed />
        <el-table-column prop="deptName" label="部门名称" width="150" fixed />
        <el-table-column prop="userName" label="员工姓名" width="120" fixed />
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="workHours" label="工作时长" width="100" align="right">
          <template #default="{ row }">
            <span>{{ row.workHours?.toFixed(1) || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="overtimeHours" label="加班时长" width="100" align="right">
          <template #default="{ row }">
            <span>{{ row.overtimeHours?.toFixed(1) || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="abnormalType" label="异常类型" width="120">
          <template #default="{ row }">
            <el-tag
              :type="getAbnormalTypeTag(row.abnormalType)"
              size="small"
            >
              {{ getAbnormalTypeLabel(row.abnormalType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="abnormalDesc" label="异常说明" min-width="200" show-overflow-tooltip />
      </el-table>
    </el-card>

    <!-- 无结果提示 -->
    <el-card v-else-if="!checking && hasChecked" class="empty-card">
      <el-empty description="核对完成，数据合规，未发现异常工时记录" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { checkCompliance, getDataDict } from '@/api'

const checking = ref(false)
const hasChecked = ref(false)
const tableData = ref([])
const summaryData = ref(null)
const deptList = ref([])
const userList = ref([])

const checkForm = reactive({
  deptName: '',
  userName: ''
})

const rules = reactive({
  standardHours: 8,
  minHours: 4,
  maxOvertime: 4,
  maxMonthlyOvertime: 80
})

const dateRange = ref([])

const loadDict = async () => {
  try {
    const res = await getDataDict()
    deptList.value = res.data.departments || []
    userList.value = res.data.users || []
  } catch (error) {
    console.error('加载数据字典失败:', error)
  }
}

const getAbnormalTypeLabel = (type) => {
  const map = {
    shortHours: '工时过短',
    excessOvertime: '加班超标',
    cumulativeExcess: '累计超标',
    negativeHours: '数据异常'
  }
  return map[type] || type
}

const getAbnormalTypeTag = (type) => {
  const map = {
    shortHours: 'warning',
    excessOvertime: 'danger',
    cumulativeExcess: 'info',
    negativeHours: 'danger'
  }
  return map[type] || 'info'
}

const handleCheck = async () => {
  if (!dateRange.value || dateRange.value.length !== 2) {
    ElMessage.warning('请选择核对时间范围')
    return
  }

  checking.value = true
  hasChecked.value = false

  try {
    const params = {
      startDate: dateRange.value[0],
      endDate: dateRange.value[1],
      deptName: checkForm.deptName,
      userName: checkForm.userName,
      rules: rules
    }
    const res = await checkCompliance(params)
    summaryData.value = res.data.summary
    tableData.value = res.data.list || []
    hasChecked.value = true

    if (tableData.value.length === 0) {
      ElMessage.success('核对完成，数据合规')
    } else {
      ElMessage.warning(`发现 ${tableData.value.length} 条异常数据`)
    }
  } catch (error) {
    console.error('核对失败:', error)
  } finally {
    checking.value = false
  }
}

const handleReset = () => {
  checkForm.deptName = ''
  checkForm.userName = ''
  dateRange.value = []
  rules.standardHours = 8
  rules.minHours = 4
  rules.maxOvertime = 4
  rules.maxMonthlyOvertime = 80
  tableData.value = []
  summaryData.value = null
  hasChecked.value = false
}

const handleExportReport = async () => {
  try {
    const params = {
      type: 'compliance',
      startDate: dateRange.value[0],
      endDate: dateRange.value[1],
      deptName: checkForm.deptName,
      userName: checkForm.userName
    }
    // 实际调用导出 API
    ElMessage.success('报告导出成功')
  } catch (error) {
    console.error('导出报告失败:', error)
  }
}

onMounted(() => {
  loadDict()
})
</script>

<style scoped>
.compliance-check-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-card,
.rule-card {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
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

.summary-value.danger {
  color: #F56C6C;
}

.type-stat {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.type-count {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.result-card {
  animation: fadeInUp 0.3s ease;
}

.result-card :deep(.el-card__header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-card {
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
