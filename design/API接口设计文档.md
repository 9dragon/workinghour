# 项目工时统计WEB软件API接口设计文档

## 一、基本信息

|字段名称|内容|
|---|---|
|文档版本|V1.0.0|
|文档作者|全栈软件开发工程师|
|创建日期|2026-01-15|
|关联文档|《架构设计说明书 V1.2.0》《需求规格书 V1.1.0》《数据库详细设计 V1.0.0》|
|协议|HTTP/HTTPS|
|数据格式|JSON（默认）/ FormData（文件上传）|
|字符编码|UTF-8|

## 二、接口概述

### 2.1 设计原则

- **RESTful风格**：遵循REST架构风格，资源导向设计
- **统一响应格式**：所有接口返回统一的JSON结构
- **JWT认证**：使用JWT令牌进行身份验证
- **版本管理**：通过URL路径进行版本控制（/api/v1/）
- **错误处理**：统一的错误码和错误消息

### 2.2 通用规范

#### 2.2.1 请求头规范

```http
# 标准请求头
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
Accept: application/json

# 文件上传请求头
Content-Type: multipart/form-data
Authorization: Bearer <JWT_TOKEN>
```

#### 2.2.2 统一响应格式

**成功响应：**
```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    // 业务数据
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**失败响应：**
```json
{
  "code": 400,
  "message": "请求参数错误",
  "error": "具体错误描述",
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

#### 2.2.3 HTTP状态码规范

|状态码|说明|使用场景|
|---|---|---|
|200|OK|请求成功|
|201|Created|资源创建成功|
|400|Bad Request|请求参数错误|
|401|Unauthorized|未认证或令牌过期|
|403|Forbidden|无权限访问|
|404|Not Found|资源不存在|
|500|Internal Server Error|服务器内部错误|

### 2.3 接口清单

|模块|接口数量|说明|
|---|---|---|
|用户认证|3|登录、登出、令牌刷新|
|数据导入|4|文件上传、记录查询、批次详情、报告下载|
|工时查询|3|项目维度、组织维度、结果导出|
|工时核对|5|完整性检查、合规性检查、核对历史、报告下载、数据字典|
|系统设置|3|数据备份、数据恢复、配置管理|
**总计**|**22**||

---

## 三、用户认证模块

### 3.1 用户登录

**接口地址：** `POST /api/v1/auth/login`

**请求参数：**

```json
{
  "username": "admin",
  "password": "password123"
}
```

|参数名|类型|必填|说明|
|---|---|---|---|
|username|string|是|登录用户名|
|password|string|是|登录密码|

**成功响应：**

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "tokenType": "Bearer",
    "expiresIn": 28800,
    "userInfo": {
      "userName": "admin",
      "realName": "系统管理员",
      "deptName": "技术部",
      "role": "admin"
    }
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**失败响应：**

```json
{
  "code": 401,
  "message": "用户名或密码错误",
  "error": "Invalid credentials",
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**错误码：**

|错误码|说明|
|---|---|
|1001|用户名或密码错误|
|1002|账号已被锁定|
|1003|账号已被禁用|

---

### 3.2 用户登出

**接口地址：** `POST /api/v1/auth/logout`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**请求参数：** 无

**成功响应：**

```json
{
  "code": 200,
  "message": "登出成功",
  "data": null,
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**说明：** 客户端删除本地存储的令牌即可，后端可选择实现令牌黑名单。

---

### 3.3 令牌刷新（可选）

**接口地址：** `POST /api/v1/auth/refresh`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**请求参数：** 无

**成功响应：**

```json
{
  "code": 200,
  "message": "令牌刷新成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "tokenType": "Bearer",
    "expiresIn": 28800
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

---

## 四、数据导入模块

### 4.1 Excel文件上传与导入

**接口地址：** `POST /api/v1/data/import`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data
```

**请求参数（FormData）：**

|参数名|类型|必填|说明|
|---|---|---|---|
|file|File|是|Excel文件（.xls或.xlsx）|
|strategy|string|否|重复数据处理策略：skip（默认）/ overwrite|

**成功响应：**

```json
{
  "code": 200,
  "message": "导入完成",
  "data": {
    "batchNo": "IMP_20260115103000_1234",
    "totalRows": 150,
    "successRows": 145,
    "repeatRows": 3,
    "invalidRows": 2,
    "errors": [
      {
        "row": 12,
        "field": "开始时间",
        "error": "时间格式错误，应为YYYY-MM-DD HH:mm:ss"
      },
      {
        "row": 25,
        "field": "工作时长",
        "error": "工作时长为负数"
      }
    ]
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**错误响应示例：**

```json
{
  "code": 400,
  "message": "文件格式错误",
  "error": "仅支持.xlsx或.xls格式的Excel文件",
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**错误码：**

|错误码|说明|
|---|---|
|2001|文件格式错误，仅支持.xlsx或.xls|
|2002|文件大小超过限制（10MB）|
|2003|文件内容为空或无法解析|
|2004|数据行数超过限制（1000行）|
|2005|必填字段缺失|
|2006|数据格式错误|

**业务规则：**
- 仅导入审批结果为"通过"且审批状态为"已完成"的记录
- 唯一性标识：姓名+开始时间+项目名称
- **同批次内**：允许同一人同一时间同一项目提交多条工时
- **跨批次**：不同批次中同一人同一时间同一项目的数据视为重复
- 默认策略：skip（跳过重复数据），可选：overwrite（覆盖重复数据）
- 生成导入批次号：格式 `IMP_YYYYMMDDHHMMSS_XXXX`

---

### 4.1.1 获取数据字典

**接口地址：** `GET /api/v1/data/dict`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**接口说明：**
从工时数据主表（work_hour_data）中动态提取不重复的项目、部门、用户列表，为前端页面的下拉选择框提供数据源。

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "projects": [
      "智慧城市平台",
      "企业管理系统",
      "移动应用开发",
      "数据分析平台"
    ],
    "departments": [
      "研发部",
      "产品部",
      "设计部",
      "运营部"
    ],
    "users": [
      {
        "userName": "张三",
        "deptName": "研发部"
      },
      {
        "userName": "李四",
        "deptName": "产品部"
      },
      {
        "userName": "王五",
        "deptName": "设计部"
      }
    ]
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**响应字段说明：**

|字段名|类型|说明|
|---|---|---|
|projects|string[]|不重复的项目名称列表|
|departments|string[]|不重复的部门名称列表|
|users|object[]|用户及部门信息列表|
|users[].userName|string|用户姓名|
|users[].deptName|string|所属部门|

**数据来源：**
- 数据表：`work_hour_data`（工时数据主表）
- 查询方式：SELECT DISTINCT 提取不重复值
- 动态更新：每次导入新的工时数据后自动更新

**使用场景：**
- 工时查询页面：项目名称、项目经理、部门名称、姓名下拉框
- 工时核对页面：部门名称、姓名下拉框
- 避免用户手动输入，确保数据一致性

**注意事项：**
- 初次使用时，如数据库无工时数据，返回空数组
- 无需手动维护数据字典，系统自动从导入的数据中提取
- 建议在进入查询页面时调用，获取最新数据

---

### 4.2 查询导入记录列表

**接口地址：** `GET /api/v1/data/records`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**查询参数：**

|参数名|类型|必填|默认值|说明|
|---|---|---|---|---|
|page|integer|否|1|页码，从1开始|
|size|integer|否|20|每页条数，支持20/50/100|
|fileName|string|否|-|文件名模糊查询|
|startDate|string|否|-|导入开始日期，格式：YYYY-MM-DD|
|endDate|string|否|-|导入结束日期，格式：YYYY-MM-DD|

**成功响应：**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "list": [
      {
        "id": 1,
        "batchNo": "IMP_20260115103000_1234",
        "fileName": "研发部_2026年1月工时.xlsx",
        "totalRows": 150,
        "successRows": 145,
        "repeatRows": 3,
        "invalidRows": 2,
        "importUser": "admin",
        "importTime": "2026-01-15T10:30:00+08:00"
      }
    ],
    "total": 100,
    "page": 1,
    "size": 20,
    "totalPages": 5
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

---

### 4.3 查询导入批次详情

**接口地址：** `GET /api/v1/import/record/{batchNo}`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**路径参数：**

|参数名|类型|必填|说明|
|---|---|---|---|
|batchNo|string|是|导入批次号|

**成功响应：**

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "id": 1,
    "batchNo": "IMP_20260116223333_1234",
    "fileName": "研发部_2026年1月工时.xlsx",
    "totalRows": 810,
    "successRows": 725,
    "repeatRows": 0,
    "invalidRows": 85,
    "importUser": "admin",
    "importTime": "2026-01-16 22:33:33",
    "fileSize": 204800,
    "duplicateStrategy": "skip",
    "errors": [
      {
        "row": 3,
        "field": "审批结果",
        "error": "审批结果为'--'，仅支持'通过'或'审批通过'"
      },
      {
        "row": 4,
        "field": "项目交付-项目名称",
        "error": "项目交付-项目名称字段为空"
      },
      {
        "row": 8,
        "field": "项目交付-工作时长",
        "error": "工作时长超过168小时（一周最大时长）"
      }
    ],
    "repeats": [
      {
        "row": 7,
        "field": "数据重复",
        "error": "序号A001、姓名张三、时间2026-01-15 09:00:00、项目智慧城市的工时数据已存在",
        "existing_batch": "IMP_20260110100000_1234"
      },
      {
        "row": 15,
        "field": "数据重复",
        "error": "序号A002、姓名李四、时间2026-01-15 14:00:00、项目管理系统的工时数据已存在",
        "existing_batch": "IMP_20260112150000_5678"
      }
    ],
    "summary": {
      "successRate": "89.5%",
      "repeatRate": "10.5%",
      "invalidRate": "10.5%"
    }
  },
  "timestamp": "2026-01-16T22:35:00"
}
```

**响应字段说明：**

|字段名|类型|说明|
|---|---|---|
|batchNo|string|导入批次号|
|fileName|string|导入的Excel文件名（原始文件名）|
|importUser|string|执行导入操作的用户名|
|importTime|string|导入时间，格式：yyyy-MM-dd HH:mm:ss|
|totalRows|number|上传文件的总数据行数|
|successRows|number|成功导入的有效数据行数|
|repeatRows|number|重复数据行数|
|invalidRows|number|无效数据行数|
|fileSize|number|导入文件大小（字节）|
|duplicateStrategy|string|重复数据处理策略（skip/cover）|
|errors|array|错误详情数组，包含所有无效数据的错误信息|
|errors[].row|number|Excel文件中的行号（包含表头，从2开始）|
|errors[].field|string|出错的字段名称|
|errors[].error|string|详细的错误原因描述|
|repeats|array|重复数据详情数组，包含所有重复数据的信息|
|repeats[].row|number|Excel文件中的行号（包含表头，从2开始）|
|repeats[].field|string|固定为"数据重复"|
|repeats[].error|string|重复数据详细描述，包含序号、姓名、时间、项目信息|
|repeats[].existing_batch|string|已存在数据所属的导入批次号|
|summary|object|导入摘要统计信息|
|summary.successRate|string|成功率（百分比）|
|summary.repeatRate|string|重复率（百分比）|
|summary.invalidRate|string|无效率（百分比）|

**重要说明：**

1. **错误详情数量**：支持返回所有错误记录，不限制100条
2. **重复数据详情**：支持返回所有重复数据记录，不限制数量
3. **错误类型**：
   - 字段为空："{字段名}字段为空"
   - 格式错误："时间格式错误"、"工作时长格式错误"
   - 取值异常："审批结果为'xxx'，仅支持'通过'或'审批通过'"
   - 范围超限："工作时长超过168小时（一周最大时长）"
4. **重复数据处理**：
   - 重复数据根据唯一性标识判定（姓名+开始时间+项目名称）
   - **同批次内**：允许同一个人在同一时间为同一项目提交多条工时记录
   - **跨批次**：不同批次的导入中，相同判定条件的数据视为重复
   - existing_batch字段显示原始数据所属的导入批次号，方便追溯
   - 处理策略由duplicateStrategy字段决定（skip跳过/cover覆盖）
5. **空数据处理**：若无错误或重复数据，errors和repeats均返回空数组[]
6. **时间格式**：importTime采用"yyyy-MM-dd HH:mm:ss"格式

**错误码：**

|错误码|说明|
|---|---|
|3001|导入记录不存在|

---

### 4.4 下载导入报告

**接口地址：** `GET /api/v1/data/records/{batchNo}/report`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**路径参数：**

|参数名|类型|必填|说明|
|---|---|---|---|
|batchNo|string|是|导入批次号|

**响应：**

- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="导入报告_{batchNo}.xlsx"`

**响应体：** Excel文件二进制流

---

### 4.5 按批次查看导入数据

**接口地址：** `GET /api/v1/data/records/{batchNo}/data`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**路径参数：**

|参数名|类型|必填|说明|
|---|---|---|---|
|batchNo|string|是|导入批次号|

**查询参数：**

|参数名|类型|必填|默认值|说明|
|---|---|---|---|---|
|page|integer|否|1|页码，从1开始|
|size|integer|否|20|每页条数，支持20/50/100|
|sortBy|string|否|start_time|排序字段：start_time/work_hours/overtime_hours|
|sortOrder|string|否|desc|排序方向：asc/desc|

**成功响应：**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "list": [
      {
        "id": 1,
        "serialNo": "001",
        "userName": "张三",
        "startTime": "2026-01-15T09:00:00+08:00",
        "endTime": "2026-01-15T18:00:00+08:00",
        "projectManager": "李经理",
        "projectName": "智慧城市平台",
        "workHours": 8.0,
        "overtimeHours": 0.0,
        "deptName": "研发部",
        "workContent": "开发功能模块"
      }
    ],
    "total": 145,
    "page": 1,
    "size": 20,
    "totalPages": 8,
    "summary": {
      "totalRecords": 145,
      "totalWorkHours": 1160.0,
      "totalOvertimeHours": 45.5,
      "userCount": 15,
      "projectCount": 8
    }
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

---

### 4.6 导出批次数据

**接口地址：** `GET /api/v1/data/records/{batchNo}/export`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**路径参数：**

|参数名|类型|必填|说明|
|---|---|---|---|
|batchNo|string|是|导入批次号|

**响应：**

- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="工时导入数据_{batchNo}.xlsx"`

**响应体：** Excel文件二进制流

---

## 五、工时查询模块

### 5.1 项目维度查询

**接口地址：** `GET /api/v1/query/project`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**查询参数：**

|参数名|类型|必填|默认值|说明|
|---|---|---|---|---|
|projectName|string|否|-|项目名称模糊查询|
|projectManager|string|否|-|项目经理模糊查询|
|startDate|string|否|-|查询开始日期，格式：YYYY-MM-DD|
|endDate|string|否|-|查询结束日期，格式：YYYY-MM-DD|
|page|integer|否|1|页码，从1开始|
|size|integer|否|20|每页条数，支持20/50/100|
|sortBy|string|否|start_time|排序字段：start_time/work_hours/overtime_hours|
|sortOrder|string|否|desc|排序方向：asc/desc|

**成功响应：**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "list": [
      {
        "id": 1,
        "serialNo": "001",
        "userName": "张三",
        "startTime": "2026-01-15T09:00:00+08:00",
        "endTime": "2026-01-15T18:00:00+08:00",
        "projectManager": "李经理",
        "projectName": "智慧城市平台",
        "workHours": 8.0,
        "overtimeHours": 0.0,
        "deptName": "研发部",
        "workContent": "开发功能模块"
      }
    ],
    "total": 50,
    "page": 1,
    "size": 20,
    "totalPages": 3,
    "summary": {
      "totalWorkHours": 400.0,
      "totalOvertimeHours": 20.0,
      "projectCount": 1,
      "userCount": 10
    }
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**错误码：**

|错误码|说明|
|---|---|
|3001|查询时间范围不能超过1年|

---

### 5.2 组织维度查询

**接口地址：** `GET /api/v1/query/organization`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**查询参数：**

|参数名|类型|必填|默认值|说明|
|---|---|---|---|---|
|deptName|string|否|-|部门名称精确查询|
|userName|string|否|-|姓名模糊查询|
|startDate|string|否|-|查询开始日期，格式：YYYY-MM-DD|
|endDate|string|否|-|查询结束日期，格式：YYYY-MM-DD|
|page|integer|否|1|页码，从1开始|
|size|integer|否|20|每页条数，支持20/50/100|
|sortBy|string|否|start_time|排序字段：start_time/work_hours/overtime_hours|
|sortOrder|string|否|desc|排序方向：asc/desc|

**成功响应：**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "list": [
      {
        "id": 1,
        "serialNo": "001",
        "userName": "张三",
        "startTime": "2026-01-15T09:00:00+08:00",
        "endTime": "2026-01-15T18:00:00+08:00",
        "projectManager": "李经理",
        "projectName": "智慧城市平台",
        "workHours": 8.0,
        "overtimeHours": 0.0,
        "deptName": "研发部",
        "workContent": "开发功能模块"
      }
    ],
    "total": 60,
    "page": 1,
    "size": 20,
    "totalPages": 3,
    "summary": {
      "totalWorkHours": 480.0,
      "totalOvertimeHours": 25.0,
      "deptCount": 1,
      "userCount": 12
    }
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**错误码：**

|错误码|说明|
|---|---|
|3001|查询时间范围不能超过1年|

---

### 5.3 导出查询结果

**接口地址：** `POST /api/v1/query/export`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**请求参数：**

```json
{
  "queryType": "project",
  "params": {
    "projectName": "智慧城市平台",
    "startDate": "2026-01-01",
    "endDate": "2026-01-31"
  }
}
```

|参数名|类型|必填|说明|
|---|---|---|---|
|queryType|string|是|查询类型：project（项目维度）/ organization（组织维度）|
|params|object|是|查询参数对象，对应查询接口的参数|

**响应：**

- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="工时查询结果_{queryType}_{timestamp}.xlsx"`

**响应体：** Excel文件二进制流

---

## 六、工时核对模块

### 6.1 工时完整性检查

**接口地址：** `POST /api/v1/check/integrity`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**请求参数：**

```json
{
  "startDate": "2026-01-01",
  "endDate": "2026-01-31",
  "deptName": "研发部",
  "userName": "张三",
  "workdays": [1, 2, 3, 4, 5]
}
```

|参数名|类型|必填|默认值|说明|
|---|---|---|---|---|
|startDate|string|是|-|核对开始日期，格式：YYYY-MM-DD|
|endDate|string|是|-|核对结束日期，格式：YYYY-MM-DD|
|deptName|string|否|-|部门名称，不传则核对所有部门|
|userName|string|否|-|人员姓名，不传则核对部门内所有人员|
|workdays|array|否|[1,2,3,4,5]|工作日定义，1-7对应周一至周日|

**业务规则：**
- 时间范围不超过3个月（约90天）
- 工作日内每个员工应至少提交一条工时记录

**成功响应：**

```json
{
  "code": 200,
  "message": "核对完成",
  "data": {
    "checkNo": "CHK_20260115103000_5678",
    "summary": {
      "totalUsers": 50,
      "missingUsers": 3,
      "totalMissingDays": 15,
      "integrityRate": 99.5
    },
    "list": [
      {
        "deptName": "研发部",
        "userName": "张三",
        "missingDates": "2026-01-10,2026-01-11,2026-01-15",
        "missingDays": 3,
        "lastSubmitDate": "2026-01-14"
      }
    ]
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**错误码：**

|错误码|说明|
|---|---|
|4001|核对时间范围不能超过3个月|
|4002|开始日期不能晚于结束日期|

---

### 6.2 工时合规性检查

**接口地址：** `POST /api/v1/check/compliance`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**请求参数：**

```json
{
  "startDate": "2026-01-01",
  "endDate": "2026-01-31",
  "deptName": "研发部",
  "userName": "张三",
  "rules": {
    "standardHours": 8,
    "minHours": 4,
    "maxOvertime": 4,
    "maxMonthlyOvertime": 80
  }
}
```

|参数名|类型|必填|默认值|说明|
|---|---|---|---|---|
|startDate|string|是|-|核对开始日期，格式：YYYY-MM-DD|
|endDate|string|是|-|核对结束日期，格式：YYYY-MM-DD|
|deptName|string|否|-|部门名称，不传则核对所有部门|
|userName|string|否|-|人员姓名，不传则核对部门内所有人员|
|rules.standardHours|number|否|8|每日标准工作时长（小时）|
|rules.minHours|number|否|4|每日工作时长下限（小时）|
|rules.maxOvertime|number|否|4|每日加班时长上限（小时）|
|rules.maxMonthlyOvertime|number|否|80|每月加班时长上限（小时）|

**业务规则：**
- 时间范围不超过3个月（约90天）
- 异常类型：工时过短、加班超标、累计超标、数据异常

**成功响应：**

```json
{
  "code": 200,
  "message": "核对完成",
  "data": {
    "checkNo": "CHK_20260115103000_5679",
    "summary": {
      "totalRecords": 1000,
      "abnormalRecords": 15,
      "abnormalUsers": 5,
      "complianceRate": 98.5,
      "invalidTypes": {
        "shortHours": 8,
        "excessOvertime": 5,
        "cumulativeExcess": 2
      }
    },
    "list": [
      {
        "deptName": "研发部",
        "userName": "张三",
        "date": "2026-01-15",
        "workHours": 3.0,
        "overtimeHours": 0.0,
        "abnormalType": "shortHours",
        "abnormalDesc": "工作时长3小时，低于下限4小时"
      }
    ]
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**错误码：**

|错误码|说明|
|---|---|
|4001|核对时间范围不能超过3个月|
|4002|开始日期不能晚于结束日期|

---

### 6.3 查询核对历史记录

**接口地址：** `GET /api/v1/check/history`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**查询参数：**

|参数名|类型|必填|默认值|说明|
|---|---|---|---|---|
|checkType|string|否|-|核对类型：integrity/compliance，不传则查询全部|
|startDate|string|否|-|核对开始日期，格式：YYYY-MM-DD|
|endDate|string|否|-|核对结束日期，格式：YYYY-MM-DD|
|page|integer|否|1|页码，从1开始|
|size|integer|否|20|每页条数，支持20/50/100|

**成功响应：**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "list": [
      {
        "id": 1,
        "checkNo": "CHK_20260115103000_5678",
        "checkType": "integrity",
        "checkTypeName": "完整性检查",
        "startDate": "2026-01-01",
        "endDate": "2026-01-31",
        "deptName": "研发部",
        "userName": null,
        "checkResult": {
          "totalUsers": 50,
          "missingUsers": 3,
          "integrityRate": 99.5
        },
        "checkUser": "admin",
        "checkTime": "2026-01-15T10:30:00+08:00"
      }
    ],
    "total": 50,
    "page": 1,
    "size": 20,
    "totalPages": 3
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

---

### 6.4 查询核对详情

**接口地址：** `GET /api/v1/check/history/{checkNo}`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**路径参数：**

|参数名|类型|必填|说明|
|---|---|---|---|
|checkNo|string|是|核对批次号|

**成功响应：**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "checkNo": "CHK_20260115103000_5678",
    "checkType": "integrity",
    "checkTypeName": "完整性检查",
    "startDate": "2026-01-01",
    "endDate": "2026-01-31",
    "deptName": "研发部",
    "userName": null,
    "checkConfig": {
      "workdays": [1, 2, 3, 4, 5],
      "excludeHolidays": false
    },
    "checkResult": {
      "totalUsers": 50,
      "missingUsers": 3,
      "totalMissingDays": 15,
      "integrityRate": 99.5,
      "details": [
        {
          "deptName": "研发部",
          "userName": "张三",
          "missingDates": "2026-01-10,2026-01-11",
          "missingDays": 2
        }
      ]
    },
    "checkUser": "admin",
    "checkTime": "2026-01-15T10:30:00+08:00",
    "reportPath": "/reports/check/CHK_20260115103000_5678.xlsx"
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**错误码：**

|错误码|说明|
|---|---|
|4011|核对批次不存在|

---

### 6.5 下载核对报告

**接口地址：** `GET /api/v1/check/history/{checkNo}/report`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**路径参数：**

|参数名|类型|必填|说明|
|---|---|---|---|
|checkNo|string|是|核对批次号|

**响应：**

- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="工时核对报告_{checkType}_{dateRange}.xlsx"`

**响应体：** Excel文件二进制流

---

### 6.6 获取数据字典

**接口地址：** `GET /api/v1/data/dict`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**请求参数：** 无

**成功响应：**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "projects": [
      "智慧城市平台",
      "企业管理系统",
      "移动应用开发",
      "数据分析平台"
    ],
    "departments": [
      "研发部",
      "产品部",
      "设计部",
      "运营部"
    ],
    "users": [
      {
        "userName": "张三",
        "deptName": "研发部"
      },
      {
        "userName": "李四",
        "deptName": "产品部"
      }
    ]
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**说明：** 此接口用于前端下拉框的数据源

---

## 七、系统设置模块

### 7.1 数据备份

**接口地址：** `GET /api/v1/settings/backup`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**请求参数：** 无

**响应：**

- Content-Type: `application/x-sqlite3` 或 `application/sql`
- Content-Disposition: `attachment; filename="workinghour_backup_{timestamp}.db"`

**响应体：** 数据库文件二进制流或SQL脚本

**说明：** 导出完整的SQLite数据库文件

---

### 7.2 数据恢复

**接口地址：** `POST /api/v1/settings/restore`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data
```

**请求参数（FormData）：**

|参数名|类型|必填|说明|
|---|---|---|---|
|file|File|是|数据库备份文件（.db或.sql）|
|confirm|string|是|确认标识，必须传"CONFIRM"以防误操作|

**成功响应：**

```json
{
  "code": 200,
  "message": "数据恢复成功",
  "data": {
    "restoreTime": "2026-01-15T10:30:00+08:00",
    "restoreUser": "admin"
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**错误响应：**

```json
{
  "code": 400,
  "message": "需要确认操作",
  "error": "请传入confirm参数并设置为'CONFIRM'以确认恢复操作",
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**错误码：**

|错误码|说明|
|---|---|
|5001|备份文件格式错误|
|5002|备份文件损坏或无法读取|
|5003|数据恢复失败，请重试|

**业务规则：**
- 恢复操作需要用户二次确认（confirm="CONFIRM"）
- 恢复前建议自动备份当前数据
- 恢复过程中系统暂停服务

---

### 7.3 获取系统配置

**接口地址：** `GET /api/v1/settings/config`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
```

**查询参数：**

|参数名|类型|必填|默认值|说明|
|---|---|---|---|---|
|category|string|否|-|配置分类：import/check/system，不传则查询全部|

**成功响应：**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "import": [
      {
        "configKey": "import.max_file_size_mb",
        "configValue": "10",
        "configType": "number",
        "description": "Excel导入文件最大大小（MB）",
        "isEditable": true
      }
    ],
    "check": [
      {
        "configKey": "check.compliance.standard_hours",
        "configValue": "8",
        "configType": "number",
        "description": "合规性检查：每日标准工作时长（小时）",
        "isEditable": true
      }
    ],
    "system": [
      {
        "configKey": "system.max_login_fails",
        "configValue": "5",
        "configType": "number",
        "description": "登录失败最大次数",
        "isEditable": true
      }
    ]
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

---

### 7.4 更新系统配置

**接口地址：** `PUT /api/v1/settings/config`

**请求头：**

```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**请求参数：**

```json
{
  "configs": [
    {
      "configKey": "import.max_file_size_mb",
      "configValue": "20"
    },
    {
      "configKey": "check.compliance.min_hours",
      "configValue": "3"
    }
  ]
}
```

|参数名|类型|必填|说明|
|---|---|---|---|
|configs|array|是|配置项数组|
|configs[].configKey|string|是|配置键|
|configs[].configValue|string|是|配置值（字符串格式）|

**成功响应：**

```json
{
  "code": 200,
  "message": "配置更新成功",
  "data": {
    "updatedCount": 2
  },
  "timestamp": "2026-01-15T10:30:00+08:00"
}
```

**错误码：**

|错误码|说明|
|---|---|
|5011|配置项不存在|
|5012|配置项不允许编辑|
|5013|配置值格式错误|

---

## 八、全局错误码定义

### 8.1 错误码分类

|错误码范围|说明|
|---|---|
|1000-1999|用户认证相关|
|2000-2999|数据导入相关|
|3000-3999|工时查询相关|
|4000-4999|工时核对相关|
|5000-5999|系统设置相关|
|9000-9999|系统级错误|

### 8.2 通用错误码

|错误码|说明|HTTP状态码|
|---|---|---|
|9000|系统内部错误|500|
|9001|请求参数错误|400|
|9002|未认证或令牌过期|401|
|9003|无权限访问|403|
|9004|资源不存在|404|
|9005|请求方法不支持|405|
|9006|请求超时|408|
|9007|服务暂时不可用|503|

### 8.3 业务错误码

详见各模块接口定义中的错误码说明。

---

## 九、分页与排序规范

### 9.1 分页参数

所有列表查询接口支持统一分页参数：

|参数名|类型|默认值|说明|
|---|---|---|---|
|page|integer|1|页码，从1开始|
|size|integer|20|每页条数，支持：20/50/100|

**分页响应格式：**

```json
{
  "data": {
    "list": [...],
    "total": 100,
    "page": 1,
    "size": 20,
    "totalPages": 5
  }
}
```

**计算公式：**
- `totalPages = Math.ceil(total / size)`

### 9.2 排序参数

所有列表查询接口支持统一排序参数：

|参数名|类型|默认值|说明|
|---|---|---|---|
|sortBy|string|按接口定义|排序字段|
|sortOrder|string|desc|排序方向：asc（升序）/ desc（降序）|

**常用排序字段：**

|接口|可选排序字段|
|---|---|
|导入记录|import_time|
|工时查询|start_time, work_hours, overtime_hours|
|核对历史|check_time|

---

## 十、JWT令牌规范

### 10.1 令牌格式

使用JWT（JSON Web Token）进行身份认证：

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyTmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzM3MDAwMDAwfQ.signature
```

### 10.2 令牌Payload结构

```json
{
  "userName": "admin",
  "realName": "系统管理员",
  "role": "admin",
  "iat": 1737000000,
  "exp": 1737028800
}
```

|字段名|说明|
|---|---|
|userName|登录用户名|
|realName|用户真实姓名|
|role|用户角色：admin/user|
|iat|令牌签发时间（Unix时间戳）|
|exp|令牌过期时间（Unix时间戳）|

### 10.3 令牌有效期

- **默认有效期：** 8小时（28800秒）
- **刷新机制：** 令牌过期后需要重新登录
- **存储方式：** 前端存储在localStorage或sessionStorage

---

## 十一、文件上传规范

### 11.1 上传限制

|限制项|限制值|说明|
|---|---|---|
|文件大小|≤10MB|Excel导入文件大小限制|
|文件格式|.xls, .xlsx|仅支持Excel格式|
|数据行数|≤1000行|单次导入数据行数限制|

### 11.2 上传请求格式

```http
POST /api/v1/data/import HTTP/1.1
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="file"; filename="工时数据.xlsx"
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

<file_binary_data>
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="strategy"

skip
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

---

## 十二、文件下载规范

### 12.1 下载响应格式

```http
HTTP/1.1 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="工时查询结果_project_20260115.xlsx"
Content-Length: 12345

<file_binary_data>
```

### 12.2 文件命名规范

|文件类型|命名格式|示例|
|---|---|---|
|导入报告|导入报告_{batchNo}.xlsx|导入报告_IMP_20260115103000_1234.xlsx|
|核对报告|工时核对报告_{checkType}_{dateRange}.xlsx|工时核对报告_integrity_20260101_20260131.xlsx|
|查询结果|工时查询结果_{queryType}_{timestamp}.xlsx|工时查询结果_project_20260115103000.xlsx|
|批次数据|工时导入数据_{batchNo}.xlsx|工时导入数据_IMP_20260115103000_1234.xlsx|
|数据库备份|workinghour_backup_{timestamp}.db|workinghour_backup_20260115103000.db|

**说明：** 文件名需要进行URL编码（encodeURIComponent）以支持中文

---

## 十三、接口调用示例

### 13.1 完整调用流程示例

#### 1. 用户登录

```javascript
// 前端调用示例
const login = async () => {
  const response = await axios.post('/api/v1/auth/login', {
    username: 'admin',
    password: 'password123'
  })

  // 保存令牌
  const { token } = response.data.data
  localStorage.setItem('token', token)

  // 设置请求拦截器
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
}
```

#### 2. Excel文件上传

```javascript
const uploadExcel = async (file, strategy) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('strategy', strategy)

  const response = await axios.post('/api/v1/data/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })

  return response.data
}
```

#### 3. 项目维度查询

```javascript
const queryByProject = async (params) => {
  const response = await axios.get('/api/v1/query/project', {
    params: {
      projectName: '智慧城市平台',
      startDate: '2026-01-01',
      endDate: '2026-01-31',
      page: 1,
      size: 20,
      sortBy: 'start_time',
      sortOrder: 'desc'
    }
  })

  return response.data
}
```

#### 4. 工时完整性检查

```javascript
const checkIntegrity = async (params) => {
  const response = await axios.post('/api/v1/check/integrity', {
    startDate: '2026-01-01',
    endDate: '2026-01-31',
    deptName: '研发部',
    workdays: [1, 2, 3, 4, 5]
  })

  return response.data
}
```

---

## 十四、接口测试说明

### 14.1 Mock数据模式

前端原型支持Mock模式，用于在没有后端的情况下进行前端开发和测试：

```javascript
// src/utils/request.js
export const MOCK_MODE = true  // 启用Mock模式

// Mock数据定义在 src/api/index.js
export const importExcel = (formData) => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '导入成功',
      data: {
        batchNo: 'BATCH' + Date.now(),
        totalRows: 100,
        successRows: 95,
        repeatRows: 3,
        invalidRows: 2
      }
    })
  }
  return request.post('/data/import', formData)
}
```

### 14.2 Postman测试集合

建议创建Postman Collection进行接口测试：

```json
{
  "info": {
    "name": "工时统计系统API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "用户认证",
      "item": [
        {
          "name": "登录",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"username\": \"admin\",\n  \"password\": \"password123\"\n}"
            },
            "url": {
              "raw": "{{base_url}}/api/v1/auth/login",
              "host": ["{{base_url}}"],
              "path": ["api", "v1", "auth", "login"]
            }
          }
        }
      ]
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:5000"
    },
    {
      "key": "token",
      "value": ""
    }
  ]
}
```

---

## 十五、接口版本管理

### 15.1 版本策略

- **URL路径版本控制：** `/api/v1/`, `/api/v2/`
- **向后兼容：** 新版本保持对旧版本的兼容
- **弃用通知：** 通过响应头提示版本弃用

```http
X-API-Version: 1.0.0
X-API-Deprecated: true
X-API-Sunset: 2026-12-31
```

### 15.2 版本升级流程

1. 在URL路径中引入新版本：`/api/v2/`
2. 保持旧版本至少6个月的兼容期
3. 在响应头中添加弃用警告
4. 更新API文档
5. 通知前端团队进行适配

---

## 十六、性能优化建议

### 16.1 接口性能目标

|接口类型|性能目标|说明|
|---|---|---|
|登录接口|≤500ms|包含JWT生成|
|文件上传|≤30s|1000行数据导入|
|列表查询|≤3s|单条件查询|
|列表查询|≤5s|多条件组合查询|
|工时核对|≤10s|100人、90天范围|

### 16.2 优化措施

1. **数据库索引优化**：为高频查询字段创建索引
2. **分页限制**：单页最大100条记录
3. **查询超时**：设置查询超时时间为30秒
4. **缓存策略**：数据字典等静态数据缓存1小时
5. **异步处理**：大批量导入采用异步任务队列

---

## 十七、安全规范

### 17.1 认证与授权

- 所有业务接口（除登录外）需要JWT令牌认证
- 令牌过期后返回401状态码
- 管理员角色（admin）可访问所有接口
- 普通用户（user）权限限制（可选实现）

### 17.2 数据校验

- 所有输入参数进行严格校验
- 使用pydantic进行数据模型验证
- SQL注入防护：使用参数化查询
- XSS防护：对用户输入进行转义

### 17.3 敏感数据保护

- 密码使用bcrypt加密存储
- 令牌签名密钥存储在环境变量中
- 日志中不记录敏感信息（密码、令牌等）
- 文件上传校验，防止恶意文件上传

---

## 十八、附录

### 18.1 完整接口清单

|模块|接口|方法|路径|认证|
|---|---|---|---|---|
|用户认证|登录|POST|/api/v1/auth/login|否|
|用户认证|登出|POST|/api/v1/auth/logout|是|
|用户认证|令牌刷新|POST|/api/v1/auth/refresh|是|
|数据导入|文件上传|POST|/api/v1/data/import|是|
|数据导入|查询记录|GET|/api/v1/data/records|是|
|数据导入|批次详情|GET|/api/v1/data/records/{batchNo}|是|
|数据导入|下载报告|GET|/api/v1/data/records/{batchNo}/report|是|
|数据导入|批次数据|GET|/api/v1/data/records/{batchNo}/data|是|
|数据导入|导出数据|GET|/api/v1/data/records/{batchNo}/export|是|
|工时查询|项目维度|GET|/api/v1/query/project|是|
|工时查询|组织维度|GET|/api/v1/query/organization|是|
|工时查询|导出结果|POST|/api/v1/query/export|是|
|工时核对|完整性检查|POST|/api/v1/check/integrity|是|
|工时核对|合规性检查|POST|/api/v1/check/compliance|是|
|工时核对|核对历史|GET|/api/v1/check/history|是|
|工时核对|核对详情|GET|/api/v1/check/history/{checkNo}|是|
|工时核对|下载报告|GET|/api/v1/check/history/{checkNo}/report|是|
|工时核对|数据字典|GET|/api/v1/data/dict|是|
|系统设置|数据备份|GET|/api/v1/settings/backup|是|
|系统设置|数据恢复|POST|/api/v1/settings/restore|是|
|系统设置|获取配置|GET|/api/v1/settings/config|是|
|系统设置|更新配置|PUT|/api/v1/settings/config|是|

**总计：22个接口**

### 18.2 字段命名转换规范

|层级|命名风格|示例|转换|
|---|---|---|---|
|数据库|蛇形(snake_case)|user_name, start_time|后端自动转换|
|后端API|蛇形(snake_case)|user_name, start_time|标准输出|
|前端|驼峰(camelCase)|userName, startTime|前端转换|

**转换示例：**

```python
# 后端：数据库字段 -> API响应
{
  "user_name": "张三",
  "start_time": "2026-01-15T09:00:00+08:00"
}

# 前端：自动转换
{
  "userName": "张三",
  "startTime": "2026-01-15T09:00:00+08:00"
}
```

### 18.3 版本变更记录

|版本号|变更时间|变更内容|变更人|
|---|---|---|---|
|V1.0.0|2026-01-15|初始API接口设计，包含22个接口的完整定义|全栈软件开发工程师|

---

**文档生成时间：** 2026-01-15
**关联文档：** 架构设计说明书 V1.2.0、需求规格书 V1.1.0、数据库详细设计 V1.0.0
