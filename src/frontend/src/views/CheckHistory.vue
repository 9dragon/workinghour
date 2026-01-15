<template>
  <div class="check-history-page">
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="核对类型">
          <el-select v-model="filterForm.checkType" placeholder="请选择" clearable style="width: 150px">
            <el-option label="完整性检查" value="integrity" />
            <el-option label="合规性检查" value="compliance" />
          </el-select>
        </el-form-item>
        <el-form-item label="核对时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="执行人">
          <el-input
            v-model="filterForm.checkUser"
            placeholder="请输入执行人"
            clearable
            style="width: 150px"
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

    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        :default-sort="{ prop: 'checkTime', order: 'descending' }"
        height="calc(100vh - 340px)"
      >
        <el-table-column prop="checkNo" label="核对批次号" width="200" fixed />
        <el-table-column label="核对类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.checkType === 'integrity' ? 'success' : 'warning'" size="small">
              {{ row.checkType === 'integrity' ? '完整性检查' : '合规性检查' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="startDate" label="核对开始日期" width="120" />
        <el-table-column prop="endDate" label="核对结束日期" width="120" />
        <el-table-column prop="deptName" label="部门" width="150" show-overflow-tooltip />
        <el-table-column prop="userName" label="人员" width="100" />
        <el-table-column prop="checkUser" label="执行人" width="100" />
        <el-table-column prop="checkTime" label="核对时间" width="160" sortable />
        <el-table-column label="核对结果摘要" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div v-if="row.checkType === 'integrity'">
              总人数: {{ row.summary.totalUsers }},
              缺失人数: {{ row.summary.missingUsers }},
              缺失天数: {{ row.summary.totalMissingDays }}
            </div>
            <div v-else>
              总记录: {{ row.summary.totalRecords }},
              异常记录: {{ row.summary.invalidRecords }},
              合规率: {{ row.summary.complianceRate }}%
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row)">
              查看详情
            </el-button>
            <el-button type="primary" link size="small" @click="handleDownloadReport(row)">
              下载报告
            </el-button>
          </template>
        </el-table-column>
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

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`核对详情 - ${currentRecord?.checkNo}`"
      width="900px"
      :close-on-click-modal="false"
    >
      <el-descriptions v-if="currentRecord" :column="2" border>
        <el-descriptions-item label="核对批次号" :span="2">{{ currentRecord.checkNo }}</el-descriptions-item>
        <el-descriptions-item label="核对类型">
          <el-tag :type="currentRecord.checkType === 'integrity' ? 'success' : 'warning'" size="small">
            {{ currentRecord.checkType === 'integrity' ? '完整性检查' : '合规性检查' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="执行人">{{ currentRecord.checkUser }}</el-descriptions-item>
        <el-descriptions-item label="核对时间范围">
          {{ currentRecord.startDate }} 至 {{ currentRecord.endDate }}
        </el-descriptions-item>
        <el-descriptions-item label="执行时间">{{ currentRecord.checkTime }}</el-descriptions-item>
        <el-descriptions-item v-if="currentRecord.deptName" label="部门">{{ currentRecord.deptName }}</el-descriptions-item>
        <el-descriptions-item v-if="currentRecord.userName" label="人员">{{ currentRecord.userName }}</el-descriptions-item>
      </el-descriptions>

      <div v-if="currentDetail && currentDetail.summary" style="margin-top: 20px">
        <el-divider>核对结果汇总</el-divider>
        <el-row v-if="currentRecord.checkType === 'integrity'" :gutter="20">
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">核对总人数</div>
              <div class="summary-value">{{ currentDetail.summary.totalUsers }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">存在缺失人数</div>
              <div class="summary-value warning">{{ currentDetail.summary.missingUsers }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">总缺失天数</div>
              <div class="summary-value danger">{{ currentDetail.summary.totalMissingDays }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">完整性百分比</div>
              <div class="summary-value highlight">{{ currentDetail.summary.integrityRate }}%</div>
            </div>
          </el-col>
        </el-row>
        <el-row v-else :gutter="20">
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">核对总记录数</div>
              <div class="summary-value">{{ currentDetail.summary.totalRecords }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">异常记录数</div>
              <div class="summary-value warning">{{ currentDetail.summary.invalidRecords }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">异常人数</div>
              <div class="summary-value danger">{{ currentDetail.summary.invalidUsers }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">合规率</div>
              <div class="summary-value highlight">{{ currentDetail.summary.complianceRate }}%</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <div v-if="currentDetail && currentDetail.list && currentDetail.list.length > 0" style="margin-top: 20px">
        <el-divider>{{ currentRecord.checkType === 'integrity' ? '缺失记录' : '异常记录' }}</el-divider>
        <el-table :data="currentDetail.list" border stripe max-height="400">
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="deptName" label="部门" width="120" />
          <el-table-column prop="userName" label="姓名" width="100" />
          <el-table-column v-if="currentRecord.checkType === 'integrity'" prop="missingDates" label="缺失日期" min-width="200" show-overflow-tooltip />
          <template v-else>
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column prop="workHours" label="工作时长" width="100" align="right" />
            <el-table-column prop="overtimeHours" label="加班时长" width="100" align="right" />
            <el-table-column prop="abnormalType" label="异常类型" width="120" />
            <el-table-column prop="abnormalDesc" label="异常说明" min-width="150" show-overflow-tooltip />
          </template>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleDownloadReport(currentRecord)">
          下载报告
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getCheckHistory, getCheckDetail, downloadCheckReport as apiDownloadReport } from '@/api'

const loading = ref(false)
const tableData = ref([])
const detailDialogVisible = ref(false)
const currentRecord = ref(null)
const currentDetail = ref(null)

const filterForm = reactive({
  checkType: '',
  checkUser: ''
})

const dateRange = ref([])

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
      size: pagination.size,
      checkType: filterForm.checkType,
      startDate: dateRange.value?.[0],
      endDate: dateRange.value?.[1],
      checkUser: filterForm.checkUser
    }
    const res = await getCheckHistory(params)
    tableData.value = res.data.list || []
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
  filterForm.checkType = ''
  filterForm.checkUser = ''
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

const handleViewDetail = async (row) => {
  currentRecord.value = row
  try {
    const res = await getCheckDetail(row.checkNo)
    currentDetail.value = res.data
  } catch (error) {
    console.error('获取详情失败:', error)
  }
  detailDialogVisible.value = true
}

const handleDownloadReport = async (row) => {
  try {
    const res = await apiDownloadReport(row.checkNo)
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const typeLabel = row.checkType === 'integrity' ? '完整性检查' : '合规性检查'
    a.download = `工时核对报告_${typeLabel}_${row.checkNo}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success('报告下载成功')
  } catch (error) {
    console.error('下载报告失败:', error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.check-history-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-card {
  margin-bottom: 0;
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
</style>
