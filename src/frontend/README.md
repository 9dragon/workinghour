# 前后端联调测试说明

## 服务状态

- **前端**: http://localhost:3000 (Vite开发服务器)
- **后端**: http://localhost:8000 (Flask API服务器)

## 配置变更

### 1. 环境配置 (.env.development)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 2. 模拟模式已关闭

`src/utils/request.js`:
```javascript
const MOCK_MODE = false  // 已关闭模拟模式
```

## API 路径映射

| 功能 | 前端调用 | 后端路由 | 状态 |
|------|----------|----------|------|
| 用户登录 | POST /auth/login | POST /api/v1/auth/login | ✅ |
| 用户登出 | POST /auth/logout | POST /api/v1/auth/logout | ✅ |
| 获取用户信息 | GET /auth/user/info | GET /api/v1/auth/user/info | ✅ |
| 获取数据字典 | GET /data/dict | GET /api/v1/data/dict | ✅ |
| 上传Excel | POST /import/upload | POST /api/v1/import/upload | ✅ |
| 导入记录列表 | GET /import/records | GET /api/v1/import/records | ✅ |
| 导入记录详情 | GET /import/record/:batchNo | GET /api/v1/import/record/:batchNo | ✅ |
| 查看导入数据 | GET /import/record/:batchNo/data | GET /api/v1/import/record/:batchNo/data | ✅ |
| 项目维度查询 | GET /query/project | GET /api/v1/query/project | ✅ |
| 组织维度查询 | GET /query/organization | GET /api/v1/query/organization | ✅ |
| 导出查询结果 | POST /query/export | POST /api/v1/query/export | ✅ |
| 完整性检查 | POST /check/integrity | POST /api/v1/check/integrity | ✅ |
| 合规性检查 | POST /check/compliance | POST /api/v1/check/compliance | ✅ |
| 核对历史 | GET /check/history | GET /api/v1/check/history | ✅ |
| 核对记录详情 | GET /check/record/:batchNo | GET /api/v1/check/record/:batchNo | ✅ |
| 获取系统配置 | GET /system/config | GET /api/v1/system/config | ✅ |
| 更新系统配置 | PUT /system/config | PUT /api/v1/system/config | ✅ |
| 数据备份 | POST /system/backup | POST /api/v1/system/backup | ✅ |
| 数据恢复 | POST /system/restore | POST /api/v1/system/restore | ✅ |
| 备份列表 | GET /system/backups | GET /api/v1/system/backups | ✅ |
| 系统信息 | GET /system/info | GET /api/v1/system/info | ✅ |

## 测试步骤

### 1. 测试登录功能

访问 http://localhost:3000/login

使用默认账户登录：
- 用户名: `admin`
- 密码: `admin123`

**预期结果**:
- 登录成功
- 跳转到首页
- 右上角显示用户名

**验证请求**:
打开浏览器开发者工具 → Network，查看：
```
POST http://localhost:8000/api/v1/auth/login
Request: {"username":"admin","password":"admin123"}
Response: {
  "code": 200,
  "data": {
    "token": "...",
    "userInfo": {
      "userName": "admin",
      "realName": "系统管理员",
      "role": "admin"
    }
  }
}
```

### 2. 测试数据字典

1. 访问"工时查询"或"工时核对"页面
2. 查看页面上的下拉选择框（项目名称、部门名称等）

**验证请求**:
```
GET http://localhost:8000/api/v1/data/dict
```

**预期结果**:
- 初次使用返回空数组：`{"projects": [], "departments": [], "users": []}`
- 导入数据后返回实际的项目、部门、用户列表
- 下拉框自动填充数据

**注意**: 数据字典是动态生成的，只有在导入工时数据后才会有内容。

### 3. 测试数据导入

1. 访问"数据导入"页面
2. 上传测试Excel文件
3. 查看导入结果

**验证请求**:
```
POST http://localhost:8000/api/v1/import/upload
Content-Type: multipart/form-data
```

### 4. 测试工时查询

1. 访问"工时查询"页面
2. 选择查询维度（项目/组织）
3. 设置筛选条件
4. 点击查询

**验证请求**:
```
GET http://localhost:8000/api/v1/query/project?page=1&size=20
或
GET http://localhost:8000/api/v1/query/organization?page=1&size=20
```

### 5. 测试工时核对

1. 访问"工时核对"页面
2. 选择核对类型（完整性/合规性）
3. 设置日期范围
4. 点击核对

**验证请求**:
```
POST http://localhost:8000/api/v1/check/integrity
Body: {
  "startDate": "2026-01-01",
  "endDate": "2026-01-31",
  "workdays": [1,2,3,4,5]
}
```

### 6. 测试系统管理

1. 访问"系统设置"页面
2. 查看系统信息
3. 修改系统配置
4. 执行数据备份

**验证请求**:
```
GET http://localhost:8000/api/v1/system/info
PUT http://localhost:8000/api/v1/system/config
POST http://localhost:8000/api/v1/system/backup
```

## 常见问题排查

### 1. 网络错误

**现象**: 前端提示"网络连接失败"

**检查**:
```bash
# 检查后端服务是否运行
curl http://localhost:8000/api/v1/system/info

# 检查CORS配置
# 后端已配置 CORS 允许跨域
```

### 2. 401 认证失败

**现象**: 请求返回 401 状态码

**检查**:
- Token 是否正确存储在 localStorage
- Token 是否在请求头中正确设置
- Token 是否过期（8小时有效期）

### 3. 数据格式不匹配

**现象**: 前端显示数据异常

**检查**:
- 查看浏览器控制台的错误信息
- 对比 API 文档中的响应格式
- 检查后端返回的实际数据结构

## 调试技巧

### 1. 查看网络请求

浏览器开发者工具 → Network → 筛选 XHR

### 2. 查看响应数据

点击具体的请求 → Response 标签页

### 3. 测试单个API

使用 curl 或 Postman 直接测试后端API：

```bash
# 登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 获取系统信息（需要token）
curl http://localhost:8000/api/v1/system/info \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. 查看后端日志

后端控制台会显示请求日志和错误信息。

### 5. 重新开启Mock模式

如果需要离线开发前端，可以重新开启Mock模式：

修改 `src/utils/request.js`:
```javascript
const MOCK_MODE = true
```

## 开发建议

1. **先测试单个功能**: 从登录开始，逐个测试每个功能模块
2. **使用浏览器插件**: 推荐 "React Developer Tools" 和 "Vue.js devtools"
3. **保持后端运行**: 开发时保持后端服务在后台运行
4. **定期检查日志**: 发现问题时先查看后端日志
5. **使用正确的测试数据**: 准备符合格式的Excel测试文件

## 下一步

完成联调测试后，可以：
1. 优化UI/UX细节
2. 添加更多的错误处理
3. 实现更多的业务功能
4. 进行性能优化
5. 准备生产环境部署
