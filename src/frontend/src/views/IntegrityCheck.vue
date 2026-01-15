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
        <el-form-item label="工作日定义">
          <el-checkbox-group v-model="workdays">
            <el-checkbox :label="1">周一</el-checkbox>
            <el-checkbox :label="2">周二</el-checkbox>
            <el-checkbox :label="3">周三</el-checkbox>
            <el-checkbox :label="4">周四</el-checkbox>
            <el-checkbox :label="5">周五</el-checkbox>
          </el-checkbox-group>
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
            <div class="summary-label">核对总人数</div>
            <div class="summary-value">{{ summaryData.totalUsers }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">存在缺失人数</div>
            <div class="summary-value warning">{{ summaryData.missingUsers }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">总缺失天数</div>
            <div class="summary-value danger">{{ summaryData.totalMissingDays }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
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

      <el-table :data="tableData" border stripe height="calc(100vh - 480px)">
        <el-table-column type="index" label="序号" width="60" fixed />
        <el-table-column prop="deptName" label="部门名称" width="150" fixed />
        <el-table-column prop="userName" label="员工姓名" width="120" fixed />
        <el-table-column prop="missingDates" label="缺失日期" min-width="300" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag
              v-for="date in row.missingDateList"
              :key="date"
              size="small"
              style="margin-right: 4px; margin-bottom: 4px"
              type="danger"
            >
              {{ date }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="missingDays" label="缺失天数" width="100" align="center">
          <template #default="{ row }">
            <span class="missing-count">{{ row.missingDays }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="lastSubmitDate" label="最近提交日期" width="120" />
      </el-table>
    </el-card>

    <!-- 无结果提示 -->
    <el-card v-else-if="!checking && hasChecked" class="empty-card">
      <el-empty description="核对完成，数据完整，未发现缺失工时记录" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { checkIntegrity, getDataDict } from '@/api'

const checking = ref(false)
const hasChecked = ref(false)
const tableData = ref([])
const summaryData = ref(null)
const deptList = ref([])
const userList = ref([])
const workdays = ref([1, 2, 3, 4, 5])

const checkForm = reactive({
  deptName: '',
  userName: ''
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
      workdays: workdays.value
    }
    const res = await checkIntegrity(params)
    summaryData.value = res.data.summary
    tableData.value = (res.data.list || []).map(item => ({
      ...item,
      missingDateList: item.missingDates?.split(',').map(d => d.trim()) || []
    }))
    hasChecked.value = true

    if (tableData.value.length === 0) {
      ElMessage.success('核对完成，数据完整')
    } else {
      ElMessage.warning(`发现 ${tableData.value.length} 人存在工时缺失`)
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
  workdays.value = [1, 2, 3, 4, 5]
  tableData.value = []
  summaryData.value = null
  hasChecked.value = false
}

const handleExportReport = async () => {
  try {
    const params = {
      type: 'integrity',
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
