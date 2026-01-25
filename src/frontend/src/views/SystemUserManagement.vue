<template>
  <div class="user-management-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><User /></el-icon>
          <span>系统用户管理</span>
        </div>
      </template>

      <!-- 说明区域 -->
      <el-alert
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #title>
          <strong>用户管理说明</strong>
        </template>
        <div style="margin-top: 8px; line-height: 1.6;">
          <p><strong>概念区分：</strong></p>
          <ul style="margin: 8px 0; padding-left: 20px;">
            <li><strong>用户</strong>：可以登录系统的账号，包含用户名、密码、角色、邮箱等认证信息</li>
            <li><strong>员工</strong>：仅包含姓名和部门信息，用于Excel导入时补充部门数据（请前往"数据管理 → 员工管理"）</li>
          </ul>
          <p style="margin-top: 8px;"><strong>用途说明：</strong></p>
          <p style="margin-left: 20px;">
            此页面用于管理系统登录用户，包括创建用户账号、分配角色（管理员/普通用户）、重置密码等操作。
          </p>
          <p style="margin-top: 8px;"><strong>注意事项：</strong></p>
          <p style="margin-left: 20px;">
            请谨慎操作，错误的用户配置可能导致系统无法正常访问。建议只由系统管理员进行此页面的维护工作。
          </p>
        </div>
      </el-alert>

      <!-- 工具栏 -->
      <div class="toolbar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户名或邮箱"
          style="width: 200px"
          clearable
          @input="handleSearch"
        />
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          添加用户
        </el-button>
      </div>

      <!-- 用户列表 -->
      <el-table :data="userList" border stripe>
        <el-table-column prop="userName" label="用户名" width="150" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
              {{ row.status === 'active' ? '正常' : '锁定' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lastLoginTime" label="最后登录时间" width="180">
          <template #default="{ row }">
            {{ row.lastLoginTime ? formatDate(row.lastLoginTime) : '从未登录' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="warning" @click="handleResetPassword(row)">重置密码</el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row)"
              :disabled="row.role === 'admin'"
            >
              删除
            </el-button>
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
      <el-form :model="formData" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="formData.userName" :disabled="isEdit" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" v-if="!isEdit">
          <el-input v-model="formData.password" type="password" placeholder="请输入密码（默认123456）" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="formData.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="formData.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="状态" v-if="isEdit">
          <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="正常" value="active" />
            <el-option label="锁定" value="locked" />
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

const userList = ref([])

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const searchKeyword = ref('')

const dialogVisible = ref(false)
const dialogTitle = ref('添加用户')
const isEdit = ref(false)

const formData = reactive({
  id: null,
  userName: '',
  password: '',
  role: 'user',
  email: '',
  status: 'active'
})

// API接口函数
const loadUsers = async () => {
  try {
    // 暂时使用模拟数据，等待后端API修复
    ElMessage.info('用户管理功能正在开发中，请稍后...')
    /*
    const res = await getSystemUsers({
      page: pagination.page,
      size: pagination.size,
      keyword: searchKeyword.value
    })
    userList.value = res.data.list
    pagination.total = res.data.total
    */
  } catch (error) {
    ElMessage.error('加载用户列表失败')
    console.error(error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadUsers()
}

const handleAdd = () => {
  dialogTitle.value = '添加用户'
  isEdit.value = false
  formData.id = null
  formData.userName = ''
  formData.password = '123456'
  formData.role = 'user'
  formData.email = ''
  formData.status = 'active'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑用户'
  isEdit.value = true
  formData.id = row.id
  formData.userName = row.userName
  formData.role = row.role
  formData.email = row.email || ''
  formData.status = row.status
  dialogVisible.value = true
}

const handleSave = async () => {
  try {
    if (!formData.userName) {
      ElMessage.warning('请输入用户名')
      return
    }

    if (!isEdit.value && !formData.password) {
      ElMessage.warning('请输入密码')
      return
    }

    // 暂时禁用保存功能
    ElMessage.info('用户管理功能正在开发中，请稍后...')
    /*
    if (isEdit.value) {
      await updateSystemUser(formData.id, {
        role: formData.role,
        email: formData.email,
        status: formData.status
      })
      ElMessage.success('更新成功')
    } else {
      await createSystemUser({
        userName: formData.userName,
        password: formData.password,
        role: formData.role,
        email: formData.email
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadUsers()
    */
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
    console.error(error)
  }
}

const handleResetPassword = (row) => {
  ElMessageBox.confirm(`确定要重置用户 "${row.userName}" 的密码为 123456 吗？`, '重置密码', {
    type: 'warning'
  }).then(async () => {
    try {
      ElMessage.info('用户管理功能正在开发中，请稍后...')
      /*
      await resetSystemUserPassword(row.id, { password: '123456' })
      ElMessage.success('密码重置成功')
      */
    } catch (error) {
      ElMessage.error(error.response?.data?.message || '重置失败')
      console.error(error)
    }
  })
}

const handleDelete = (row) => {
  if (row.role === 'admin') {
    ElMessage.warning('不能删除管理员用户')
    return
  }

  ElMessageBox.confirm(`确定要删除用户 "${row.userName}" 吗？`, '提示', {
    type: 'warning'
  }).then(async () => {
    try {
      ElMessage.info('用户管理功能正在开发中，请稍后...')
      /*
      await deleteSystemUser(row.id)
      ElMessage.success('删除成功')
      loadUsers()
      */
    } catch (error) {
      ElMessage.error(error.response?.data?.message || '删除失败')
      console.error(error)
    }
  })
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
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
