<template>
  <div class="work-hours-check-page">
    <el-card class="filter-card">
      <el-form :model="checkForm" inline>
        <el-form-item label="核对时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期（可选）"
            end-placeholder="结束日期（可选）"
            value-format="YYYY-MM-DD"
            style="width: 260px"
            clearable
          />
        </el-form-item>
        <el-form-item label="部门">
          <el-select
            v-model="checkForm.deptName"
            placeholder="请选择部门（可选）"
            clearable
            filterable
            style="width: 200px"
            @change="handleDeptChange"
          >
            <el-option
              v-for="item in dataDict.departments"
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
              v-for="item in filteredUsers"
              :key="item.userName"
              :label="item.userName"
              :value="item.userName"
            />
          </el-select>
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
            <div class="summary-label">核对总工单数</div>
            <div class="summary-value">{{ summaryData.totalSerials }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">正常工单数</div>
            <div class="summary-value normal">{{ summaryData.normalSerials }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">偏低工单数</div>
            <div class="summary-value warning">{{ summaryData.shortSerials }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">偏高工单数</div>
            <div class="summary-value danger">{{ summaryData.excessSerials }}</div>
          </div>
        </el-col>
      </el-row>

      <!-- 合规率 -->
      <el-row :gutter="20" style="margin-top: 16px">
        <el-col :span="24">
          <div class="summary-item rate-item">
            <div class="summary-label">合规率</div>
            <div class="summary-value highlight">{{ summaryData.complianceRate.toFixed(2) }}%</div>
          </div>
        </el-col>
      </el-row>

      <el-divider>各工时类型统计</el-divider>

      <!-- 分类型统计 -->
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="type-stat-item">
            <div class="type-label">项目交付</div>
            <div class="type-value">{{ summaryData.workTypeStats.project_delivery.totalHours }}h</div>
            <div class="type-avg">平均: {{ summaryData.workTypeStats.project_delivery.avgHours }}h</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="type-stat-item">
            <div class="type-label">产研项目</div>
            <div class="type-value">{{ summaryData.workTypeStats.product_research.totalHours }}h</div>
            <div class="type-avg">平均: {{ summaryData.workTypeStats.product_research.avgHours }}h</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="type-stat-item">
            <div class="type-label">售前支持</div>
            <div class="type-value">{{ summaryData.workTypeStats.presales_support.totalHours }}h</div>
            <div class="type-avg">平均: {{ summaryData.workTypeStats.presales_support.avgHours }}h</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="type-stat-item">
            <div class="type-label">部门内务</div>
            <div class="type-value">{{ summaryData.workTypeStats.dept_internal.totalHours }}h</div>
            <div class="type-avg">平均: {{ summaryData.workTypeStats.dept_internal.avgHours }}h</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 核对结果 -->
    <el-card v-if="abnormalData.length > 0" class="result-card">
      <template #header>
        <div class="card-header">
          <el-icon><Document /></el-icon>
          <span>核对结果</span>
        </div>
      </template>

      <el-table
        :data="abnormalData"
        border
        stripe
        height="calc(100vh - 600px)"
        :default-sort="{ prop: 'startTime', order: 'descending' }"
      >
        <el-table-column type="index" label="序号" width="60" fixed />
        <el-table-column prop="serialNo" label="工单序号" width="100" fixed />
        <el-table-column prop="userName" label="员工姓名" width="100" fixed />
        <el-table-column prop="startTime" label="开始时间" width="120" />
        <el-table-column prop="endTime" label="结束时间" width="120" />
        <el-table-column prop="projectDeliveryHours" label="项目交付(h)" width="120" align="right">
          <template #default="{ row }">
            <span v-if="row.projectDeliveryHours > 0">{{ row.projectDeliveryHours }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="productResearchHours" label="产研项目(h)" width="120" align="right">
          <template #default="{ row }">
            <span v-if="row.productResearchHours > 0">{{ row.productResearchHours }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="presalesSupportHours" label="售前支持(h)" width="120" align="right">
          <template #default="{ row }">
            <span v-if="row.presalesSupportHours > 0">{{ row.presalesSupportHours }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="deptInternalHours" label="部门内务(h)" width="120" align="right">
          <template #default="{ row }">
            <span v-if="row.deptInternalHours > 0">{{ row.deptInternalHours }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="totalWorkHours" label="工作时长总和(h)" width="150" align="right">
          <template #default="{ row }">
            <strong>{{ row.totalWorkHours }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="leaveHours" label="请假时长(h)" width="120" align="right">
          <template #default="{ row }">
            <span v-if="row.leaveHours > 0">{{ row.leaveHours }}</span>
            <span v-else class="text-gray">0</span>
          </template>
        </el-table-column>
        <el-table-column prop="expectedWorkHours" label="应工作时长(h)" width="140" align="right">
          <template #default="{ row }">
            <strong>{{ row.expectedWorkHours }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="legalWorkHours" label="法定工作时间(h)" width="150" align="right">
          <template #default="{ row }">
            {{ row.legalWorkHours }}
          </template>
        </el-table-column>
        <el-table-column prop="difference" label="差值(h)" width="120" align="right">
          <template #default="{ row }">
            <span
              :class="{
                'text-success': row.difference === 0,
                'text-warning': row.difference < 0,
                'text-danger': row.difference > 0
              }"
            >
              {{ row.difference > 0 ? '+' : '' }}{{ row.difference }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'normal' ? 'success' : row.status === 'short' ? 'warning' : 'danger'"
              size="small"
            >
              {{ row.status === 'normal' ? '正常' : row.status === 'short' ? '偏低' : '偏高' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 无结果提示 -->
    <el-card v-else-if="!checking && hasChecked" class="empty-card">
      <el-empty description="核对完成，所有工单工作时长均正常" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { checkWorkHoursConsistency, getDataDict } from '@/api'

const checking = ref(false)
const hasChecked = ref(false)
const tableData = ref([])
const summaryData = ref(null)
const dataDict = ref({
  departments: [],
  users: []
})
const checkNo = ref('')

const checkForm = reactive({
  deptName: '',
  userName: ''
})

const dateRange = ref([])

const filteredUsers = computed(() => {
  if (!checkForm.deptName) {
    return dataDict.value.users
  }
  return dataDict.value.users.filter(user => user.deptName === checkForm.deptName)
})

// 只显示异常数据（不显示正常工单）
const abnormalData = computed(() => {
  return tableData.value.filter(item => item.status !== 'normal')
})

const loadDict = async () => {
  try {
    const res = await getDataDict()
    dataDict.value.departments = res.data.departments || []
    dataDict.value.users = res.data.users || []
  } catch (error) {
    console.error('加载数据字典失败:', error)
  }
}

const handleDeptChange = () => {
  checkForm.userName = ''
}

const handleCheck = async () => {
  // 时间范围改为可选，不做必填校验

  checking.value = true
  hasChecked.value = false

  try {
    const params = {
      startDate: dateRange.value?.[0] || null,
      endDate: dateRange.value?.[1] || null,
      deptName: checkForm.deptName || null,
      userName: checkForm.userName || null
    }
    const res = await checkWorkHoursConsistency(params)
    summaryData.value = res.data.summary
    tableData.value = res.data.list || []
    checkNo.value = res.data.checkNo
    hasChecked.value = true

    // 统计异常数据
    const abnormalCount = tableData.value.filter(item => item.status !== 'normal').length

    if (abnormalCount === 0) {
      ElMessage.success('核对完成，所有工单工作时长均正常')
    } else {
      const shortCount = tableData.value.filter(item => item.status === 'short').length
      const excessCount = tableData.value.filter(item => item.status === 'excess').length
      ElMessage.warning(`发现 ${shortCount} 个工单偏低，${excessCount} 个工单偏高`)
    }
  } catch (error) {
    ElMessage.error(error.message || '核对失败')
    console.error('核对失败:', error)
  } finally {
    checking.value = false
  }
}

const handleReset = () => {
  checkForm.deptName = ''
  checkForm.userName = ''
  dateRange.value = []
  tableData.value = []
  summaryData.value = null
  hasChecked.value = false
  checkNo.value = ''
}

onMounted(() => {
  loadDict()
})
</script>

<style scoped>
.work-hours-check-page {
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

.summary-item.rate-item {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.summary-item.rate-item .summary-label {
  color: rgba(255, 255, 255, 0.9);
}

.summary-item.rate-item .summary-value {
  color: #fff;
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
  color: #67C23A;
}

.summary-value.normal {
  color: #67C23A;
}

.summary-value.warning {
  color: #E6A23C;
}

.summary-value.danger {
  color: #F56C6C;
}

.type-stat-item {
  text-align: center;
  padding: 12px;
  background-color: #fafafa;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.type-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
}

.type-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.type-avg {
  font-size: 12px;
  color: #909399;
}

.result-card {
  animation: fadeInUp 0.3s ease;
}

.result-card :deep(.el-card__header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.text-gray {
  color: #909399;
}

.text-success {
  color: #67C23A;
  font-weight: 600;
}

.text-warning {
  color: #E6A23C;
  font-weight: 600;
}

.text-danger {
  color: #F56C6C;
  font-weight: 600;
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
