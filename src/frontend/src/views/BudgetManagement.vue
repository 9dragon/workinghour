<template>
  <div class="budget-management-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><Edit /></el-icon>
          <span>预算录入管理</span>
        </div>
      </template>

      <!-- 说明区域 -->
      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #title>
          <strong>预算录入说明</strong>
        </template>
        <div style="margin-top: 8px; line-height: 1.6;">
          <p>在此页面录入和管理项目工时预算。预算按项目、类型分别录入。</p>
          <p style="margin-top: 8px;"><strong>重要提示：</strong></p>
          <ul style="margin: 8px 0; padding-left: 20px;">
            <li>同一项目、同一类型只能有一条预算记录</li>
            <li>预算工时必须为非负数（单位：人天）</li>
            <li>预算录入后可在"预算统计"页面查看执行情况</li>
          </ul>
        </div>
      </el-alert>

      <!-- 工具栏 -->
      <div class="toolbar">
        <el-input
          v-model="filters.projectCode"
          placeholder="筛选项目代码"
          style="width: 200px"
          clearable
          @input="loadBudgets"
        />
        <el-select
          v-model="filters.budgetType"
          placeholder="筛选类型"
          style="width: 150px"
          clearable
          @change="loadBudgets"
        >
          <el-option label="项目管理" value="project_manager" />
          <el-option label="数采实施" value="data_collection" />
          <el-option label="软件实施" value="software_dev" />
        </el-select>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          添加预算
        </el-button>
      </div>

      <!-- 预算列表 -->
      <el-table :data="budgetList" border stripe>
        <el-table-column prop="projectCode" label="项目代码" width="120" />
        <el-table-column prop="projectName" label="项目名称" width="200" />
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
        <el-table-column prop="createdAt" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="loadBudgets"
        @size-change="loadBudgets"
        style="margin-top: 20px; display: flex; justify-content: flex-end"
      />
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="formData" label-width="100px">
        <el-form-item label="项目代码">
          <el-select
            v-if="!isEdit"
            v-model="formData.projectCode"
            filterable
            placeholder="请选择项目代码"
            style="width: 100%"
          >
            <el-option
              v-for="project in projectList"
              :key="project.projectCode"
              :label="`${project.projectCode} - ${project.projectName}`"
              :value="project.projectCode"
            />
          </el-select>
          <el-input v-else v-model="formData.projectCode" disabled />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="formData.budgetType" placeholder="请选择类型" style="width: 100%">
            <el-option label="项目管理" value="project_manager" />
            <el-option label="数采实施" value="data_collection" />
            <el-option label="软件实施" value="software_dev" />
          </el-select>
        </el-form-item>
        <el-form-item label="预算工时">
          <el-input-number
            v-model="formData.budgetHours"
            :min="0"
            :precision="2"
            :step="1"
            style="width: 100%"
          />
          <span style="margin-left: 8px">人天</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getBudgets, createBudget, updateBudget, deleteBudget, getProjects } from '@/api'

const budgetList = ref([])
const projectList = ref([])

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const filters = reactive({
  projectCode: '',
  budgetType: ''
})

const dialogVisible = ref(false)
const dialogTitle = ref('添加预算')
const isEdit = ref(false)

const formData = reactive({
  id: null,
  projectCode: '',
  budgetType: '',
  budgetHours: 0
})

const loadBudgets = async () => {
  try {
    const res = await getBudgets({
      page: pagination.page,
      size: pagination.size,
      projectCode: filters.projectCode,
      budgetType: filters.budgetType
    })
    budgetList.value = res.data.list
    pagination.total = res.data.total
  } catch (error) {
    ElMessage.error('加载预算列表失败')
    console.error(error)
  }
}

const loadProjects = async () => {
  try {
    const res = await getProjects({
      page: 1,
      size: 1000,
      projectType: 'delivery'  // 只获取项目交付类
    })
    projectList.value = res.data.list || []
  } catch (error) {
    console.error('Failed to load projects:', error)
  }
}

const handleAdd = () => {
  dialogTitle.value = '添加预算'
  isEdit.value = false
  formData.id = null
  formData.projectCode = ''
  formData.budgetType = ''
  formData.budgetHours = 0
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑预算'
  isEdit.value = true
  formData.id = row.id
  formData.projectCode = row.projectCode
  formData.budgetType = row.budgetType
  formData.budgetHours = row.budgetHours
  dialogVisible.value = true
}

const handleSave = async () => {
  try {
    if (!formData.projectCode) {
      ElMessage.warning('请选择项目代码')
      return
    }
    if (!formData.budgetType) {
      ElMessage.warning('请选择类型')
      return
    }
    if (formData.budgetHours < 0) {
      ElMessage.warning('预算工时不能为负数')
      return
    }

    if (isEdit.value) {
      await updateBudget(formData.id, {
        budgetHours: formData.budgetHours
      })
      ElMessage.success('更新成功')
    } else {
      await createBudget({
        projectCode: formData.projectCode,
        budgetType: formData.budgetType,
        budgetHours: formData.budgetHours
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadBudgets()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
    console.error(error)
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该预算吗？', '提示', {
    type: 'warning'
  }).then(async () => {
    try {
      await deleteBudget(row.id)
      ElMessage.success('删除成功')
      loadBudgets()
    } catch (error) {
      ElMessage.error(error.response?.data?.message || '删除失败')
      console.error(error)
    }
  })
}

const getRoleTagType = (role) => {
  const typeMap = {
    project_manager: 'success',
    data_collection: 'warning',
    software_dev: 'primary'
  }
  return typeMap[role] || 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadBudgets()
  loadProjects()
})
</script>

<style scoped>
.budget-management-page {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.toolbar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
</style>
