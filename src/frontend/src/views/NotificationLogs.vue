<template>
  <div class="notification-logs-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><Bell /></el-icon>
          <span>通知发送日志</span>
          <span class="hint-text">记录每次定时检查 + 通知分发的结果</span>
        </div>
      </template>

      <!-- 查询条件 -->
      <el-form :inline="true" :model="query" class="filter-form">
        <el-form-item label="渠道">
          <el-select v-model="query.channel" placeholder="全部" clearable style="width: 120px">
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="邮件" value="email" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 140px">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
            <el-option label="跳过" value="skipped" />
          </el-select>
        </el-form-item>

        <el-form-item label="员工">
          <el-input v-model="query.employeeName" placeholder="姓名" clearable style="width: 140px" />
        </el-form-item>

        <el-form-item label="检查批次">
          <el-input v-model="query.checkNo" placeholder="checkNo" clearable style="width: 220px" />
        </el-form-item>

        <el-form-item label="发送时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="-"
            start-placeholder="开始"
            end-placeholder="结束"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 列表 -->
      <div class="table-toolbar">
        <el-button
          type="danger"
          :disabled="selectedLogs.length === 0"
          @click="handleBatchDelete"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
        <span v-if="selectedLogs.length" class="selection-info">
          已选 {{ selectedLogs.length }} 条
        </span>
      </div>
      <el-table
        :data="list"
        v-loading="loading"
        stripe
        border
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="sentAt" label="发送时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.sentAt) }}
          </template>
        </el-table-column>
        <el-table-column prop="employeeName" label="员工" width="120" />
        <el-table-column prop="deptName" label="部门" width="140" />
        <el-table-column prop="channel" label="渠道" width="100">
          <template #default="{ row }">
            <el-tag :type="row.channel === 'dingtalk' ? 'primary' : 'success'" size="small">
              {{ channelLabel(row.channel) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="errorMessage" label="错误/跳过原因" show-overflow-tooltip />
        <el-table-column prop="checkNo" label="检查批次" width="220">
          <template #default="{ row }">
            <el-link v-if="row.checkNo" type="primary" @click="goCheckDetail(row.checkNo)">
              {{ row.checkNo }}
            </el-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              :disabled="!row.content"
              @click="openContent(row)"
            >
              查看内容
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.size"
        :page-sizes="[20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 16px; justify-content: flex-end"
        @size-change="loadList"
        @current-change="loadList"
      />

      <!-- 通知内容查看弹窗 -->
      <el-dialog
        v-model="contentDialogVisible"
        :title="contentDialogTitle"
        width="720px"
        destroy-on-close
      >
        <pre class="content-pre">{{ contentDialogText }}</pre>
        <template #footer>
          <el-button @click="contentDialogVisible = false">关闭</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getNotificationLogs,
  deleteNotificationLog,
  batchDeleteNotificationLogs
} from '@/api'

const router = useRouter()
const loading = ref(false)
const list = ref([])
const total = ref(0)
const dateRange = ref([])
const selectedLogs = ref([])

const query = reactive({
  page: 1,
  size: 20,
  channel: '',
  status: '',
  employeeName: '',
  checkNo: '',
  startDate: '',
  endDate: ''
})

const channelLabel = (c) => ({ dingtalk: '钉钉', email: '邮件' }[c] || c || '-')
const statusLabel = (s) => ({ success: '成功', failed: '失败', skipped: '跳过' }[s] || s || '-')
const statusType = (s) => ({ success: 'success', failed: 'danger', skipped: 'warning' }[s] || 'info')

const formatTime = (iso) => {
  if (!iso) return '-'
  return iso.replace('T', ' ').split('.')[0]
}

const loadList = async () => {
  loading.value = true
  try {
    query.startDate = dateRange.value?.[0] || ''
    query.endDate = dateRange.value?.[1] || ''
    const res = await getNotificationLogs(query)
    list.value = res.data?.list || []
    total.value = res.data?.total || 0
  } catch (error) {
    console.error('加载通知日志失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  query.page = 1
  loadList()
}

const handleReset = () => {
  query.channel = ''
  query.status = ''
  query.employeeName = ''
  query.checkNo = ''
  dateRange.value = []
  query.page = 1
  loadList()
}

const goCheckDetail = (checkNo) => {
  router.push(`/check/detail/${checkNo}`)
}

const handleSelectionChange = (val) => {
  selectedLogs.value = val
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该日志吗？', '提示', { type: 'warning' })
    .then(async () => {
      try {
        await deleteNotificationLog(row.id)
        ElMessage.success('删除成功')
        if (list.value.length === 1 && query.page > 1) {
          query.page -= 1
        }
        await loadList()
      } catch (error) {
        ElMessage.error(error.response?.data?.message || '删除失败')
        console.error(error)
      }
    })
    .catch(() => {})
}

const handleBatchDelete = () => {
  if (selectedLogs.value.length === 0) {
    ElMessage.warning('请先选择要删除的日志')
    return
  }
  const count = selectedLogs.value.length
  ElMessageBox.confirm(`确定要删除选中的 ${count} 条日志吗？`, '提示', { type: 'warning' })
    .then(async () => {
      try {
        await batchDeleteNotificationLogs(selectedLogs.value.map(l => l.id))
        ElMessage.success(`成功删除 ${count} 条日志`)
        selectedLogs.value = []
        if (list.value.length === count && query.page > 1) {
          query.page -= 1
        }
        await loadList()
      } catch (error) {
        ElMessage.error(error.response?.data?.message || '删除失败')
        console.error(error)
      }
    })
    .catch(() => {})
}

const contentDialogVisible = ref(false)
const contentDialogTitle = ref('')
const contentDialogText = ref('')

const openContent = (row) => {
  contentDialogTitle.value = `${channelLabel(row.channel)} 通知内容 - ${row.employeeName} (${formatTime(row.sentAt)})`
  contentDialogText.value = row.content || ''
  contentDialogVisible.value = true
}

onMounted(() => {
  loadList()
})
</script>

<style scoped>
.notification-logs-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.hint-text {
  font-size: 12px;
  color: #909399;
  margin-left: 12px;
  font-weight: normal;
}

.filter-form {
  margin-bottom: 8px;
}

.table-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.selection-info {
  font-size: 13px;
  color: #606266;
}

.content-pre {
  max-height: 60vh;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  background: #fafafa;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Consolas', 'Microsoft YaHei', monospace;
  font-size: 13px;
  line-height: 1.6;
  margin: 0;
}
</style>
