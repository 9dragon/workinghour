<template>
  <div class="integrity-check-page">
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
        <el-col :span="4">
          <div class="summary-item">
            <div class="summary-label">核对总人数</div>
            <div class="summary-value">{{ summaryData.totalUsers }}</div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="summary-item">
            <div class="summary-label">存在空缺人数</div>
            <div class="summary-value warning">{{ summaryData.missingUsers }}</div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="summary-item">
            <div class="summary-label">总空缺工作日天数</div>
            <div class="summary-value danger">{{ summaryData.totalMissingWorkdays }}</div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="summary-item">
            <div class="summary-label">存在重复人数</div>
            <div class="summary-value info">{{ summaryData.duplicateUsers }}</div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="summary-item">
            <div class="summary-label">总重复工作日天数</div>
            <div class="summary-value info">{{ summaryData.totalDuplicateWorkdays }}</div>
          </div>
        </el-col>
      </el-row>
      <el-row :gutter="20" style="margin-top: 16px">
        <el-col :span="24">
          <div class="summary-item rate-item">
            <div class="summary-label">完整性百分比</div>
            <div class="summary-value highlight">{{ summaryData.integrityRate.toFixed(2) }}%</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 核对结果 -->
    <el-card v-if="tableData.length > 0" class="result-card">
      <template #header>
        <div class="card-header">
          <el-icon><Document /></el-icon>
          <span>核对结果</span>
          <el-button type="primary" size="small" @click="handleExportReport">
            <el-icon><Download /></el-icon>
            导出报告
          </el-button>
        </div>
      </template>

      <el-table :data="tableData" border stripe height="calc(100vh - 500px)">
        <el-table-column type="index" label="序号" width="60" fixed />
        <el-table-column prop="deptName" label="部门名称" width="150" fixed />
        <el-table-column prop="userName" label="员工姓名" width="120" fixed />
        <el-table-column prop="issueType" label="问题类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.issueType === 'missing' ? 'danger' : 'warning'" size="small">
              {{ row.issueType === 'missing' ? '空缺' : '重复' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="serialNo" label="工单序号" width="120">
          <template #default="{ row }">
            <span v-if="row.issueType === 'duplicate'">{{ row.serialNo }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="gapStartDate" label="开始日期" width="120" />
        <el-table-column prop="gapEndDate" label="结束日期" width="120" />
        <el-table-column prop="affectedWorkdays" label="影响工作日天数" width="140" align="center">
          <template #default="{ row }">
            <span :class="row.issueType === 'missing' ? 'missing-count' : 'duplicate-count'">
              {{ row.affectedWorkdays }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
      </el-table>
    </el-card>

    <!-- 无结果提示 -->
    <el-card v-else-if="!checking && hasChecked" class="empty-card">
      <el-empty description="核对完成，数据完整，未发现空缺或重复记录" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { checkIntegrityConsistency, getDataDict } from '@/api'

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
  if (!checkForm.value.deptName) {
    return dataDict.value.users
  }
  return dataDict.value.users.filter(user => user.deptName === checkForm.value.deptName)
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
      deptName: checkForm.deptName || null,
      userName: checkForm.userName || null
    }
    const res = await checkIntegrityConsistency(params)
    summaryData.value = res.data.summary
    tableData.value = res.data.list || []
    checkNo.value = res.data.checkNo
    hasChecked.value = true

    if (tableData.value.length === 0) {
      ElMessage.success('核对完成，数据完整')
    } else {
      const missingCount = tableData.value.filter(item => item.issueType === 'missing').length
      const duplicateCount = tableData.value.filter(item => item.issueType === 'duplicate').length
      ElMessage.warning(`发现 ${missingCount} 人存在空缺，${duplicateCount} 人存在重复`)
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

const handleExportReport = async () => {
  try {
    if (!checkNo.value) {
      ElMessage.warning('请先执行核对操作')
      return
    }
    const { downloadCheckReport } = await import('@/api')
    await downloadCheckReport(checkNo.value)
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
.integrity-check-page {
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

.summary-value.warning {
  color: #E6A23C;
}

.summary-value.danger {
  color: #F56C6C;
}

.summary-value.info {
  color: #409EFF;
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

.missing-count {
  color: #F56C6C;
  font-weight: 600;
}

.duplicate-count {
  color: #E6A23C;
  font-weight: 600;
}

.text-gray {
  color: #909399;
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
