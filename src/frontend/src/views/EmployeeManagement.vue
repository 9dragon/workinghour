<template>
  <div class="user-management-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><User /></el-icon>
          <span>员工部门管理</span>
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
          <strong>员工管理说明</strong>
        </template>
        <div style="margin-top: 8px; line-height: 1.6;">
          <p><strong>概念区分：</strong></p>
          <ul style="margin: 8px 0; padding-left: 20px;">
            <li><strong>员工</strong>：仅包含姓名和部门信息，用于 Excel 导入时自动补充缺失的部门数据</li>
            <li><strong>用户</strong>：可以登录系统的账号，用于身份认证和权限管理（请前往"系统管理 → 用户管理"）</li>
          </ul>
          <p style="margin-top: 8px;"><strong>用途说明：</strong></p>
          <p style="margin-left: 20px;">
            当从钉钉导出的 Excel 文件中某些工时记录的"创建人部门"字段为空时，系统会自动根据员工姓名匹配并补充此页面维护的部门信息。
          </p>
          <p style="margin-top: 8px;"><strong>维护方式：</strong></p>
          <p style="margin-left: 20px;">
            由数据管理员手动维护，请确保员工姓名与钉钉导出文件中的姓名完全一致，部门信息准确无误。
          </p>
        </div>
      </el-alert>

      <!-- 工具栏 -->
      <div class="toolbar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索姓名或部门"
          style="width: 200px"
          clearable
          @input="handleSearch"
        />
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          添加员工
        </el-button>
      </div>

      <!-- 用户列表 -->
      <el-table :data="employeeList" border stripe>
        <el-table-column prop="employeeName" label="姓名" width="150" />
        <el-table-column prop="deptName" label="部门" width="200">
          <template #default="{ row }">
            <el-tag v-if="row.deptName">{{ row.deptName }}</el-tag>
            <el-tag v-else type="danger">未配置</el-tag>
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
import { getEmployees, createEmployee, updateEmployee, deleteEmployee } from '@/api'

const employeeList = ref([])
const deptList = ref([])  // 部门列表（自动聚合）

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const searchKeyword = ref('')

const dialogVisible = ref(false)
const dialogTitle = ref('添加员工')
const isEdit = ref(false)

const formData = reactive({
  id: null,
  employeeName: '',
  deptName: ''
})

const loadUsers = async () => {
  try {
    const res = await getEmployees({
      page: pagination.page,
      size: pagination.size,
      keyword: searchKeyword.value
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

const handleSearch = () => {
  pagination.page = 1
  loadUsers()
}

const handleAdd = () => {
  dialogTitle.value = '添加员工'
  isEdit.value = false
  formData.id = null
  formData.employeeName = ''
  formData.deptName = ''
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑员工'
  isEdit.value = true
  formData.id = row.id
  formData.employeeName = row.employeeName
  formData.deptName = row.deptName || ''
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
        deptName: formData.deptName
      })
      ElMessage.success('更新成功')
    } else {
      await createEmployee({
        employeeName: formData.employeeName,
        deptName: formData.deptName
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

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.user-management-page {
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
</style>
