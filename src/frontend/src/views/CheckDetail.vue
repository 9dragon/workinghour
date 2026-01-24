<template>
  <div class="check-detail-page">
    <!-- 页面头部 -->
    <el-page-header @back="goBack" title="返回" :content="`核对详情 - ${checkNo}`" />

    <!-- 加载状态 -->
    <div v-loading="loading" style="min-height: 400px">
      <template v-if="detail">
        <!-- 基本信息 -->
        <el-card class="info-card">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="核对批次号" :span="2">{{ detail.checkNo }}</el-descriptions-item>
            <el-descriptions-item label="核对类型">
              <el-tag :type="getCheckTypeTag(detail.checkType)" size="small">
                {{ getCheckTypeLabel(detail.checkType) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="触发方式">
              <el-tag :type="getTriggerTypeTag(detail.triggerType)" size="small">
                {{ getTriggerTypeLabel(detail.triggerType) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="执行人">{{ detail.checkUser }}</el-descriptions-item>
            <el-descriptions-item label="执行时间">{{ formatCheckTime(detail.checkTime) }}</el-descriptions-item>
            <el-descriptions-item label="核对时间范围">
              <span v-if="detail.startDate && detail.endDate">
                {{ detail.startDate }} 至 {{ detail.endDate }}
              </span>
              <span v-else class="text-gray">全量查询（所有数据）</span>
            </el-descriptions-item>
            <el-descriptions-item v-if="detail.deptName" label="部门">{{ detail.deptName }}</el-descriptions-item>
            <el-descriptions-item v-if="detail.userName" label="人员">{{ detail.userName }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 核对结果汇总 -->
        <el-card v-if="detail.checkResult" class="summary-card">
          <template #header>
            <div class="card-header">核对结果汇总</div>
          </template>

          <!-- 周报提交检查汇总 -->
          <el-row v-if="detail.checkType === 'integrity-consistency' || detail.checkType === 'integrity'" :gutter="20">
            <el-col :span="4">
              <div class="summary-item">
                <div class="summary-label">核对总人数</div>
                <div class="summary-value">{{ detail.checkResult.totalUsers }}</div>
              </div>
            </el-col>
            <el-col :span="5">
              <div class="summary-item">
                <div class="summary-label">存在空缺人数</div>
                <div class="summary-value warning">{{ detail.checkResult.missingUsers }}</div>
              </div>
            </el-col>
            <el-col :span="5">
              <div class="summary-item">
                <div class="summary-label">总空缺工作日天数</div>
                <div class="summary-value danger">{{ detail.checkResult.totalMissingWorkdays || detail.checkResult.totalMissingDays }}</div>
              </div>
            </el-col>
            <el-col :span="5">
              <div class="summary-item">
                <div class="summary-label">存在重复人数</div>
                <div class="summary-value info">{{ detail.checkResult.duplicateUsers || 0 }}</div>
              </div>
            </el-col>
            <el-col :span="5">
              <div class="summary-item">
                <div class="summary-label">总重复工作日天数</div>
                <div class="summary-value info">{{ detail.checkResult.totalDuplicateWorkdays || 0 }}</div>
              </div>
            </el-col>
          </el-row>

          <!-- 工作时长检查汇总 -->
          <el-row v-else :gutter="20">
            <el-col :span="6">
              <div class="summary-item">
                <div class="summary-label">核对总工单数</div>
                <div class="summary-value">{{ detail.checkResult.totalSerials }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-item">
                <div class="summary-label">正常工单数</div>
                <div class="summary-value normal">{{ detail.checkResult.normalSerials }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-item">
                <div class="summary-label">偏低工单数</div>
                <div class="summary-value warning">{{ detail.checkResult.shortSerials }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-item">
                <div class="summary-label">偏高工单数</div>
                <div class="summary-value danger">{{ detail.checkResult.excessSerials }}</div>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <!-- 异常记录列表 -->
        <el-card v-if="detail.list && detail.list.length > 0" class="detail-card">
          <template #header>
            <div class="card-header">
              {{ detail.checkType === 'integrity-consistency' ? '问题记录' : '异常记录' }}
              （共 {{ detail.list.length }} 条）
            </div>
          </template>

          <el-table :data="paginatedList" border stripe max-height="600px">
            <el-table-column type="index" label="序号" width="60" />
            <el-table-column prop="deptName" label="部门" width="120" />
            <el-table-column prop="userName" label="姓名" width="100" />

            <!-- 周报提交检查列 -->
            <template v-if="detail.checkType === 'integrity-consistency' || detail.checkType === 'integrity'">
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

          <!-- 分页 -->
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.size"
              :page-sizes="[20, 50, 100, 200]"
              :total="detail.list.length"
              layout="total, sizes, prev, pager, next, jumper"
              small
            />
          </div>
        </el-card>

        <!-- 无异常记录提示 -->
        <el-card v-else class="detail-card">
          <el-empty description="恭喜！本次核对未发现异常记录" />
        </el-card>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getCheckDetail } from '@/api'

const route = useRoute()
const router = useRouter()
const checkNo = route.params.checkNo
const loading = ref(false)
const detail = ref(null)

const pagination = reactive({
  page: 1,
  size: 10
})

const paginatedList = computed(() => {
  if (!detail.value?.list) return []
  const start = (pagination.page - 1) * pagination.size
  const end = start + pagination.size
  return detail.value.list.slice(start, end)
})

const loadDetail = async () => {
  loading.value = true
  try {
    const res = await getCheckDetail(checkNo)
    detail.value = res.data
  } catch (error) {
    ElMessage.error('获取详情失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.back()
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

const formatCheckTime = (timeStr) => {
  if (!timeStr) return ''
  return timeStr.replace('T', ' ').substring(0, 19)
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.check-detail-page {
  padding: 20px;
}

.info-card, .summary-card, .detail-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
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

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
