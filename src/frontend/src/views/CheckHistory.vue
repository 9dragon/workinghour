<template>
  <div class="check-history-page">
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="核对类型">
          <el-select v-model="filterForm.checkType" placeholder="请选择" clearable style="width: 180px">
            <el-option label="周报提交检查" value="integrity-consistency" />
            <el-option label="工作时长检查" value="work-hours-consistency" />
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
        <el-table-column label="核对类型" width="200" align="center">
          <template #default="{ row }">
            <el-tag :type="getCheckTypeTag(row.checkType)" size="small">
              {{ getCheckTypeLabel(row.checkType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="触发方式" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getTriggerTypeTag(row.triggerType)" size="small">
              {{ getTriggerTypeLabel(row.triggerType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="startDate" label="核对开始日期" width="120" />
        <el-table-column prop="endDate" label="核对结束日期" width="120" />
        <el-table-column prop="deptName" label="部门" width="150" show-overflow-tooltip />
        <el-table-column prop="userName" label="人员" width="100" />
        <el-table-column prop="checkUser" label="执行人" width="100" />
        <el-table-column prop="checkTime" label="核对时间" width="160" sortable class-name="sortable-column" />
        <el-table-column label="核对结果摘要" min-width="250" show-overflow-tooltip>
          <template #default="{ row }">
            <div v-if="row.checkResult">
              <div v-if="row.checkType === 'integrity-consistency' || row.checkType === 'integrity'">
                总人数: {{ row.checkResult.totalUsers }},
                空缺人数: {{ row.checkResult.missingUsers }},
                重复人数: {{ row.checkResult.duplicateUsers || 0 }}
              </div>
              <div v-else>
                总工单: {{ row.checkResult.totalSerials }},
                偏低工单: {{ row.checkResult.shortSerials }},
                偏高工单: {{ row.checkResult.excessSerials }}
              </div>
            </div>
            <div v-else class="text-gray">暂无数据</div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row)">
              查看详情
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
          <el-tag :type="getCheckTypeTag(currentRecord.checkType)" size="small">
            {{ getCheckTypeLabel(currentRecord.checkType) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="触发方式">
          <el-tag :type="getTriggerTypeTag(currentRecord.triggerType)" size="small">
            {{ getTriggerTypeLabel(currentRecord.triggerType) }}
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

      <div v-if="currentDetail && currentDetail.checkResult" style="margin-top: 20px">
        <el-divider>核对结果汇总</el-divider>
        <el-row v-if="currentRecord.checkType === 'integrity-consistency' || currentRecord.checkType === 'integrity'" :gutter="20">
          <el-col :span="4">
            <div class="summary-item">
              <div class="summary-label">核对总人数</div>
              <div class="summary-value">{{ currentDetail.checkResult.totalUsers }}</div>
            </div>
          </el-col>
          <el-col :span="5">
            <div class="summary-item">
              <div class="summary-label">存在空缺人数</div>
              <div class="summary-value warning">{{ currentDetail.checkResult.missingUsers }}</div>
            </div>
          </el-col>
          <el-col :span="5">
            <div class="summary-item">
              <div class="summary-label">总空缺工作日天数</div>
              <div class="summary-value danger">{{ currentDetail.checkResult.totalMissingWorkdays || currentDetail.checkResult.totalMissingDays }}</div>
            </div>
          </el-col>
          <el-col :span="5">
            <div class="summary-item">
              <div class="summary-label">存在重复人数</div>
              <div class="summary-value info">{{ currentDetail.checkResult.duplicateUsers || 0 }}</div>
            </div>
          </el-col>
          <el-col :span="5">
            <div class="summary-item">
              <div class="summary-label">总重复工作日天数</div>
              <div class="summary-value info">{{ currentDetail.checkResult.totalDuplicateWorkdays || 0 }}</div>
            </div>
          </el-col>
        </el-row>
        <el-row v-else :gutter="20">
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">核对总工单数</div>
              <div class="summary-value">{{ currentDetail.checkResult.totalSerials }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">正常工单数</div>
              <div class="summary-value normal">{{ currentDetail.checkResult.normalSerials }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">偏低工单数</div>
              <div class="summary-value warning">{{ currentDetail.checkResult.shortSerials }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">偏高工单数</div>
              <div class="summary-value danger">{{ currentDetail.checkResult.excessSerials }}</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <div v-if="currentDetail && currentDetail.list && currentDetail.list.length > 0" style="margin-top: 20px">
        <el-divider>{{ currentRecord.checkType === 'integrity-consistency' ? '问题记录' : '异常记录' }}</el-divider>
        <el-table :data="currentDetail.list" border stripe max-height="400">
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="deptName" label="部门" width="120" />
          <el-table-column prop="userName" label="姓名" width="100" />

          <!-- 周报提交检查列 -->
          <template v-if="currentRecord.checkType === 'integrity-consistency'">
            <el-table-column prop="issueType" label="问题类型" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.issueType === 'missing' ? 'danger' : 'warning'" size="small">
                  {{ row.issueType === 'missing' ? '空缺' : '重复' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="gapStartDate" label="开始日期" width="120" />
            <el-table-column prop="gapEndDate" label="结束日期" width="120" />
            <el-table-column prop="affectedWorkdays" label="影响工作日天数" width="140" align="center" />
            <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
          </template>

          <!-- 工作时长检查列 -->
          <template v-else>
            <el-table-column prop="serialNo" label="工单序号" width="100" />
            <el-table-column prop="startTime" label="开始时间" width="120" />
            <el-table-column prop="endTime" label="结束时间" width="120" />
            <el-table-column prop="totalWorkHours" label="工作时长总和(h)" width="140" align="right" />
            <el-table-column prop="expectedWorkHours" label="应工作时長(h)" width="120" align="right" />
            <el-table-column prop="legalWorkHours" label="法定工作时间(h)" width="140" align="right" />
            <el-table-column prop="difference" label="差值(h)" width="100" align="right">
              <template #default="{ row }">
                <span :class="{
                  'text-success': row.difference === 0,
                  'text-warning': row.difference < 0,
                  'text-danger': row.difference > 0
                }">
                  {{ row.difference > 0 ? '+' : '' }}{{ row.difference }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'normal' ? 'success' : row.status === 'short' ? 'warning' : 'danger'" size="small">
                  {{ row.status === 'normal' ? '正常' : row.status === 'short' ? '偏低' : '偏高' }}
                </el-tag>
              </template>
            </el-table-column>
          </template>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getCheckHistory, getCheckDetail } from '@/api'

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
  size: 10,
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

const getCheckTypeLabel = (type) => {
  const map = {
    'integrity-consistency': '周报提交检查',
    'work-hours-consistency': '工作时长检查',
    'integrity': '周报提交检查',
    'compliance': '工作时长检查'
  }
  return map[type] || type
}

const getCheckTypeTag = (type) => {
  const map = {
    'integrity-consistency': 'success',
    'work-hours-consistency': 'warning',
    'integrity': 'success',
    'compliance': 'warning'
  }
  return map[type] || 'info'
}

const getTriggerTypeLabel = (type) => {
  const map = {
    'manual': '手动触发',
    'scheduled': '定时触发',
    'import': '导入后触发'
  }
  return map[type] || '未知'
}

const getTriggerTypeTag = (type) => {
  const map = {
    'manual': 'primary',
    'scheduled': 'success',
    'import': 'warning'
  }
  return map[type] || 'info'
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

.summary-value.normal {
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

.text-gray {
  color: #909399;
}

:deep(.sortable-column .cell) {
  white-space: nowrap;
  overflow: visible;
}

:deep(.sortable-column .cell .caret-wrapper) {
  margin-left: 4px;
}
</style>
