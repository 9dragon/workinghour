<template>
  <div class="user-management-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><User /></el-icon>
          <span>员工管理</span>
        </div>
      </template>

      <!-- 说明区域 -->
      <el-collapse style="margin-bottom: 12px">
        <el-collapse-item name="1">
          <template #title>
            <strong>📖 员工管理说明</strong>
          </template>
          <div class="collapse-content" style="line-height: 1.6;">
            <p><strong>概念区分：</strong></p>
            <ul style="margin: 8px 0; padding-left: 20px;">
              <li><strong>员工</strong>：指工时填报中的员工，用于工时统计</li>
              <li><strong>用户</strong>：可以登录系统的账号，用于身份认证和权限管理（请前往"系统管理 → 用户管理"）</li>
            </ul>
            <p style="margin-top: 8px;"><strong>维护方式：</strong></p>
            <p style="margin-left: 20px;">
              Excel数据导入时自动记录员工基本信息，管理员可以手动维护员工角色和工时分类匹配
            </p>
          </div>
        </el-collapse-item>
      </el-collapse>

      <!-- 筛选查询区域 -->
      <el-form :model="filterForm" inline class="filter-form">
        <el-form-item label="姓名">
          <el-input
            v-model="filterForm.searchKeyword"
            placeholder="请输入姓名"
            clearable
            style="width: 150px"
          />
        </el-form-item>

        <el-form-item label="部门">
          <el-select
            v-model="filterForm.deptFilter"
            placeholder="请选择部门"
            clearable
            filterable
            style="width: 150px"
          >
            <el-option
              v-for="dept in deptList"
              :key="dept"
              :label="dept"
              :value="dept"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="角色">
          <el-select
            v-model="filterForm.roleFilter"
            placeholder="请选择角色"
            clearable
            style="width: 150px"
          >
            <el-option label="项目管理" value="project_manager" />
            <el-option label="数采实施" value="data_collection" />
            <el-option label="软件实施" value="software_dev" />
            <el-option label="普通员工" value="staff" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleQuery">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 工具栏 -->
      <div class="toolbar">
        <div style="flex: 1"></div>
        <el-button
          type="warning"
          :disabled="selectedEmployees.length === 0"
          @click="handleBatchEdit"
        >
          批量编辑角色 ({{ selectedEmployees.length }})
        </el-button>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          添加员工
        </el-button>
      </div>

      <!-- 用户列表 -->
      <el-table :data="employeeList" border stripe style="width: 100%" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="employeeName" label="姓名" min-width="120" />
        <el-table-column prop="deptName" label="部门" min-width="150">
          <template #default="{ row }">
            <el-tag v-if="row.deptName">{{ row.deptName }}</el-tag>
            <el-tag v-else type="danger">未配置</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="120">
          <template #default="{ row }">
            <el-tag v-if="row.role" :type="getRoleTagType(row.role)">
              {{ row.roleLabel || getRoleLabel(row.role) }}
            </el-tag>
            <el-tag v-else type="info">普通员工</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
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
        @current-change="loadUsers"
        @size-change="loadUsers"
        style="margin-top: 20px; display: flex; justify-content: flex-end"
      />
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="formData" label-width="80px">
        <el-form-item label="姓名">
          <el-input v-model="formData.employeeName" :disabled="isEdit" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="部门">
          <el-select
            v-model="formData.deptName"
            filterable
            allow-create
            default-first-option
            placeholder="请选择或输入部门"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="dept in deptList"
              :key="dept"
              :label="dept"
              :value="dept"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="formData.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="项目管理" value="project_manager" />
            <el-option label="数采实施" value="data_collection" />
            <el-option label="软件实施" value="software_dev" />
            <el-option label="普通员工" value="staff" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量编辑对话框 -->
    <el-dialog v-model="batchDialogVisible" title="批量编辑角色" width="400px">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 12px"
      >
        已选择 {{ selectedEmployees.length }} 位员工
      </el-alert>
      <el-form :model="batchFormData" label-width="80px">
        <el-form-item label="新角色">
          <el-select v-model="batchFormData.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="项目管理" value="project_manager" />
            <el-option label="数采实施" value="data_collection" />
            <el-option label="软件实施" value="software_dev" />
            <el-option label="普通员工" value="staff" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchSave">确定更新</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getEmployees, createEmployee, updateEmployee, deleteEmployee, updateEmployeeRole, batchUpdateEmployeeRoles } from '@/api'

const employeeList = ref([])
const deptList = ref([])  // 部门列表（自动聚合）

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const filterForm = reactive({
  searchKeyword: '',
  roleFilter: '',
  deptFilter: ''
})
const selectedEmployees = ref([])

const dialogVisible = ref(false)
const dialogTitle = ref('添加员工')
const isEdit = ref(false)

const formData = reactive({
  id: null,
  employeeName: '',
  deptName: '',
  role: 'staff'
})

const batchDialogVisible = ref(false)
const batchFormData = reactive({
  role: 'staff'
})

const loadUsers = async () => {
  try {
    const res = await getEmployees({
      page: pagination.page,
      size: pagination.size,
      keyword: filterForm.searchKeyword,
      role: filterForm.roleFilter,
      dept: filterForm.deptFilter
    })
    employeeList.value = res.data.list
    pagination.total = res.data.total

    // 聚合部门列表
    const depts = new Set()
    employeeList.value.forEach(emp => {
      if (emp.deptName) {
        depts.add(emp.deptName)
      }
    })
    deptList.value = Array.from(depts).sort()
  } catch (error) {
    ElMessage.error('加载员工列表失败')
    console.error(error)
  }
}

const handleSelectionChange = (selection) => {
  selectedEmployees.value = selection
}

const handleQuery = () => {
  pagination.page = 1
  selectedEmployees.value = []
  loadUsers()
}

const handleReset = () => {
  filterForm.searchKeyword = ''
  filterForm.deptFilter = ''
  filterForm.roleFilter = ''
  pagination.page = 1
  selectedEmployees.value = []
  loadUsers()
}

const handleAdd = () => {
  dialogTitle.value = '添加员工'
  isEdit.value = false
  formData.id = null
  formData.employeeName = ''
  formData.deptName = ''
  formData.role = 'staff'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑员工'
  isEdit.value = true
  formData.id = row.id
  formData.employeeName = row.employeeName
  formData.deptName = row.deptName || ''
  formData.role = row.role || 'staff'
  dialogVisible.value = true
}

const handleSave = async () => {
  try {
    if (!formData.employeeName) {
      ElMessage.warning('请输入姓名')
      return
    }

    if (isEdit.value) {
      await updateEmployee(formData.id, {
        deptName: formData.deptName,
        role: formData.role
      })
      ElMessage.success('更新成功')
    } else {
      await createEmployee({
        employeeName: formData.employeeName,
        deptName: formData.deptName,
        role: formData.role
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadUsers()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
    console.error(error)
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该员工吗？', '提示', {
    type: 'warning'
  }).then(async () => {
    try {
      await deleteEmployee(row.id)
      ElMessage.success('删除成功')
      loadUsers()
    } catch (error) {
      ElMessage.error(error.response?.data?.message || '删除失败')
      console.error(error)
    }
  })
}

const handleBatchEdit = () => {
  if (selectedEmployees.value.length === 0) {
    ElMessage.warning('请先选择要编辑的员工')
    return
  }

  // 默认使用第一个选中员工的角色
  batchFormData.role = selectedEmployees.value[0].role || 'staff'
  batchDialogVisible.value = true
}

const handleBatchSave = async () => {
  try {
    if (!batchFormData.role) {
      ElMessage.warning('请选择角色')
      return
    }

    // 使用批量更新接口
    const employeeIds = selectedEmployees.value.map(emp => emp.id)
    await batchUpdateEmployeeRoles({
      employeeIds,
      role: batchFormData.role
    })

    ElMessage.success(`成功更新 ${selectedEmployees.value.length} 位员工的角色`)
    batchDialogVisible.value = false
    selectedEmployees.value = []
    loadUsers()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '批量更新失败')
    console.error(error)
  }
}

const getRoleLabel = (role) => {
  const labels = {
    project_manager: '项目管理',
    data_collection: '数采实施',
    software_dev: '软件实施',
    staff: '普通员工'
  }
  return labels[role] || '未知'
}

const getRoleTagType = (role) => {
  const typeMap = {
    project_manager: 'success',
    data_collection: 'warning',
    software_dev: 'primary',
    staff: 'info'
  }
  return typeMap[role] || 'info'
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.user-management-page {
  padding: 20px;
  width: 100%;
}

.user-management-page :deep(.el-card) {
  width: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.filter-form {
  --el-form-item-margin-bottom: 8px;
  margin-bottom: 8px;
}

.toolbar {
  align-items: center;
  min-height: 32px;
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.collapse-content {
    padding: 8px 12px;
  background-color: #fdf6ec;
  border-radius: 4px;
}
</style>
