<template>
  <div class="project-management-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><FolderOpened /></el-icon>
          <span>项目管理</span>
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
          <strong>项目管理说明</strong>
        </template>
        <div style="margin-top: 8px; line-height: 1.6;">
          <p><strong>项目识别规则：</strong></p>
          <ul style="margin: 8px 0; padding-left: 20px;">
            <li><strong>D 开头</strong>：项目交付类（如：D4086）</li>
            <li><strong>P 开头</strong>：产研项目类（如：P1234）</li>
            <li><strong>其他</strong>：其他项目类</li>
          </ul>
          <p style="margin-top: 8px;"><strong>管理方式：</strong></p>
          <p style="margin-left: 20px;">
            项目信息独立管理，支持手动创建或从工时数据中自动提取。项目经理信息可与工时记录关联。
          </p>
        </div>
      </el-alert>

      <!-- 工具栏 -->
      <div class="toolbar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索项目代码或名称"
          style="width: 200px"
          clearable
          @input="handleSearch"
        />
        <el-select
          v-model="statusFilter"
          placeholder="筛选状态"
          style="width: 150px"
          clearable
          @change="loadProjects"
        >
          <el-option label="进行中" value="active" />
          <el-option label="已完成" value="completed" />
          <el-option label="已暂停" value="suspended" />
        </el-select>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          添加项目
        </el-button>
      </div>

      <!-- 项目列表 -->
      <el-table :data="projectList" border stripe>
        <el-table-column prop="projectCode" label="项目代码" width="120">
          <template #default="{ row }">
            <el-tag :type="getPrefixTagType(row.projectPrefix)" size="small">
              {{ row.projectPrefix }}
            </el-tag>
            <span style="margin-left: 4px;">{{ row.projectCode }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="projectName" label="项目名称" width="250" />
        <el-table-column label="项目类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.projectType)">
              {{ row.projectTypeLabel }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="projectManager" label="项目经理" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ row.statusLabel }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="170" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">详情</el-button>
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
        @current-change="loadProjects"
        @size-change="loadProjects"
        style="margin-top: 20px; display: flex; justify-content: flex-end"
      />
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="formData" label-width="100px">
        <el-form-item label="项目代码">
          <el-input v-model="formData.projectCode" :disabled="isEdit" placeholder="如：D4086、P1234" />
        </el-form-item>
        <el-form-item label="项目名称">
          <el-input v-model="formData.projectName" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目类型">
          <el-select v-model="formData.projectType" placeholder="请选择项目类型" style="width: 100%">
            <el-option label="项目交付" value="delivery" />
            <el-option label="产研项目" value="research" />
            <el-option label="其他项目" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目经理">
          <el-input v-model="formData.projectManager" placeholder="请输入项目经理姓名" />
        </el-form-item>
        <el-form-item label="状态" v-if="isEdit">
          <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="进行中" value="active" />
            <el-option label="已完成" value="completed" />
            <el-option label="已暂停" value="suspended" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="项目详情" width="600px">
      <div v-if="currentProject" class="project-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="项目代码">{{ currentProject.projectCode }}</el-descriptions-item>
          <el-descriptions-item label="项目名称">{{ currentProject.projectName }}</el-descriptions-item>
          <el-descriptions-item label="项目类型">
            <el-tag :type="getTypeTagType(currentProject.projectType)">
              {{ currentProject.projectTypeLabel }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(currentProject.status)">
              {{ currentProject.statusLabel }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="项目经理">{{ currentProject.projectManager || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ currentProject.createdAt }}</el-descriptions-item>
        </el-descriptions>

        <div class="stats-section" style="margin-top: 20px;">
          <h4>工时统计</h4>
          <el-row :gutter="20" v-if="currentProject.stats">
            <el-col :span="8">
              <el-statistic title="总工时" :value="currentProject.stats.totalHours" :precision="2" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="总加班时长" :value="currentProject.stats.totalOvertime" :precision="2" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="记录数" :value="currentProject.stats.recordCount" />
            </el-col>
          </el-row>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProjects, getProjectDetail, createProject, updateProject, deleteProject } from '@/api'

const projectList = ref([])

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const searchKeyword = ref('')
const typeFilter = ref('')
const statusFilter = ref('')

const dialogVisible = ref(false)
const dialogTitle = ref('添加项目')
const isEdit = ref(false)

const formData = reactive({
  id: null,
  projectCode: '',
  projectName: '',
  projectType: '',
  projectManager: '',
  status: 'active'
})

const detailDialogVisible = ref(false)
const currentProject = ref(null)

const loadProjects = async () => {
  try {
    const res = await getProjects({
      page: pagination.page,
      size: pagination.size,
      projectCode: searchKeyword.value,
      projectType: 'delivery',  // 只显示项目交付类，不显示产研项目
      status: statusFilter.value
    })
    projectList.value = res.data.list
    pagination.total = res.data.total
  } catch (error) {
    ElMessage.error('加载项目列表失败')
    console.error(error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadProjects()
}

const handleAdd = () => {
  dialogTitle.value = '添加项目'
  isEdit.value = false
  formData.id = null
  formData.projectCode = ''
  formData.projectName = ''
  formData.projectType = ''
  formData.projectManager = ''
  formData.status = 'active'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑项目'
  isEdit.value = true
  formData.id = row.id
  formData.projectCode = row.projectCode
  formData.projectName = row.projectName
  formData.projectType = row.projectType
  formData.projectManager = row.projectManager || ''
  formData.status = row.status
  dialogVisible.value = true
}

const handleSave = async () => {
  try {
    if (!formData.projectCode) {
      ElMessage.warning('请输入项目代码')
      return
    }
    if (!formData.projectName) {
      ElMessage.warning('请输入项目名称')
      return
    }
    if (!formData.projectType) {
      ElMessage.warning('请选择项目类型')
      return
    }

    if (isEdit.value) {
      await updateProject(formData.id, {
        projectName: formData.projectName,
        projectManager: formData.projectManager,
        status: formData.status
      })
      ElMessage.success('更新成功')
    } else {
      await createProject({
        projectCode: formData.projectCode,
        projectName: formData.projectName,
        projectType: formData.projectType,
        projectManager: formData.projectManager,
        status: formData.status
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadProjects()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
    console.error(error)
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该项目吗？', '提示', {
    type: 'warning'
  }).then(async () => {
    try {
      await deleteProject(row.id)
      ElMessage.success('删除成功')
      loadProjects()
    } catch (error) {
      ElMessage.error(error.response?.data?.message || '删除失败')
      console.error(error)
    }
  })
}

const handleView = async (row) => {
  try {
    const res = await getProjectDetail(row.id)
    currentProject.value = res.data
    detailDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取项目详情失败')
    console.error(error)
  }
}

const getPrefixTagType = (prefix) => {
  const typeMap = {
    'D': 'success',
    'P': 'warning',
    'O': 'info'
  }
  return typeMap[prefix] || 'info'
}

const getTypeTagType = (type) => {
  const typeMap = {
    'delivery': 'success',
    'research': 'warning',
    'other': 'info'
  }
  return typeMap[type] || 'info'
}

const getStatusTagType = (status) => {
  const typeMap = {
    'active': 'success',
    'completed': 'info',
    'suspended': 'warning'
  }
  return typeMap[status] || 'info'
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.project-management-page {
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
}

.stats-section h4 {
  margin: 0 0 15px 0;
  font-size: 14px;
  color: #606266;
}
</style>
