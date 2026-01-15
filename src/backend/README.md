# 工时统计系统 - 后端服务

基于 Flask 的工时统计系统后端服务，提供 RESTful API 接口用于数据导入、查询、核对和系统管理。

## 技术栈

- **框架**: Flask 3.1.2
- **数据库**: SQLite 3
- **ORM**: SQLAlchemy 3.1.1
- **认证**: JWT (PyJWT 2.6.0)
- **数据处理**: pandas 2.0.3, openpyxl 3.1.2
- **数据验证**: Pydantic 2.4.2
- **密码加密**: bcrypt 4.0.1

## 项目结构

```
backend/
├── app/
│   ├── __init__.py              # Flask 应用工厂
│   ├── models/                  # 数据模型
│   │   ├── db.py                # 数据库实例
│   │   ├── user.py              # 用户模型
│   │   ├── work_hour_data.py    # 工时数据模型
│   │   ├── import_record.py     # 导入记录模型
│   │   ├── check_record.py      # 核对记录模型
│   │   └── sys_config.py        # 系统配置模型
│   ├── routes/                  # 路由模块
│   │   ├── auth.py              # 用户认证
│   │   ├── import_data.py       # 数据导入
│   │   ├── query.py             # 工时查询
│   │   ├── check.py             # 工时核对
│   │   └── system.py            # 系统管理
│   └── utils/                   # 工具函数
│       ├── response.py          # 统一响应格式
│       ├── jwt_utils.py         # JWT 工具
│       ├── helpers.py           # 辅助函数
│       └── schemas.py           # 数据验证模型
├── instance/                    # 运行时目录
│   ├── workinghour.db           # SQLite 数据库文件
│   └── uploads/                 # 临时上传文件目录
├── backups/                     # 数据库备份目录
├── config.py                    # 配置文件
├── requirements.txt             # Python 依赖
├── run.py                       # 应用入口
└── .env.example                 # 环境变量示例
```

## 快速开始

### 1. 环境要求

- Python 3.9+
- pip

### 2. 安装依赖

```bash
cd src/backend
pip install -r requirements.txt
```

### 3. 配置环境变量（可选）

```bash
cp .env.example .env
# 编辑 .env 文件，修改相关配置
```

### 4. 启动服务

```bash
python run.py
```

服务将在 `http://localhost:8000` 启动。

### 5. 默认账户

系统启动时会自动创建两个默认账户：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| test | test123 | 普通用户 |

**⚠️ 重要**: 生产环境部署前请修改默认密码！

## API 接口文档

### 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token (JWT)
- **响应格式**: JSON

### 统一响应格式

**成功响应**:
```json
{
  "code": 200,
  "message": "操作成功",
  "data": {},
  "timestamp": "2024-01-15T10:30:00"
}
```

**错误响应**:
```json
{
  "code": 1001,
  "message": "错误描述",
  "timestamp": "2024-01-15T10:30:00"
}
```

### 业务错误码

| 错误码 | 说明 |
|--------|------|
| 1001 | 用户名不能为空 |
| 1002 | 密码错误 |
| 1003 | 用户名或密码错误 |
| 1004 | 账号已锁定 |
| 2001 | 未上传文件 |
| 2002 | 文件格式错误 |
| 2003 | 文件解析失败 |
| 2004 | 文件行数超限 |
| 3001 | 记录不存在 |
| 4001 | 日期范围错误 |
| 5001 | 配置项不存在 |
| 5002 | 配置项只读 |
| 5003 | 配置值类型错误 |
| 6001 | 备份文件未指定 |
| 6002 | 备份文件不存在 |

### API 接口列表

**共计 20 个接口**，分为 6 大功能模块：

#### 1. 用户认证 (3个)

**1.1 用户登录**
```
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

响应:
{
  "code": 200,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "tokenType": "Bearer",
    "expiresIn": 28800,
    "userInfo": {
      "userName": "admin",
      "realName": "系统管理员",
      "role": "admin"
    }
  }
}
```

**1.2 用户登出**
```
POST /api/v1/auth/logout
Authorization: Bearer {token}
```

**1.3 获取用户信息**
```
GET /api/v1/auth/user/info
Authorization: Bearer {token}
```

#### 2. 数据导入 (5个)

**2.1 获取数据字典**
```
GET /api/v1/data/dict
Authorization: Bearer {token}

响应:
{
  "code": 200,
  "data": {
    "projects": ["智慧城市平台", "企业管理系统", "移动应用开发"],
    "departments": ["研发部", "产品部", "设计部", "运营部"],
    "users": [
      {"userName": "张三", "deptName": "研发部"},
      {"userName": "李四", "deptName": "产品部"}
    ]
  }
}
```

**说明**:
- 从工时数据中动态提取不重复的项目、部门、用户列表
- 用于前端页面的下拉选择框
- 数据随着导入的工时数据自动更新

**2.2 上传 Excel 文件**
```
POST /api/v1/import/upload
Content-Type: multipart/form-data
Authorization: Bearer {token}

参数:
- file: Excel 文件 (.xlsx 或 .xls)
- duplicateStrategy: 重复数据处理策略 (skip/cover)

响应:
{
  "code": 200,
  "data": {
    "batchNo": "IMP_20240115103000_1234",
    "totalRows": 100,
    "successRows": 95,
    "repeatRows": 3,
    "invalidRows": 2,
    "errors": [...]
  }
}
```

**2.3 获取导入记录列表**
```
GET /api/v1/import/records?page=1&size=20
Authorization: Bearer {token}
```

**2.4 获取导入记录详情**
```
GET /api/v1/import/record/{batchNo}
Authorization: Bearer {token}
```

**2.5 查看导入批次数据**
```
GET /api/v1/import/record/{batchNo}/data?page=1&size=20
Authorization: Bearer {token}
```

#### 3. 工时查询 (3个)

**3.1 按项目维度查询**
```
GET /api/v1/query/project?projectName=xxx&projectManager=xxx&startDate=2024-01-01&endDate=2024-01-31&page=1&size=20
Authorization: Bearer {token}
```

**3.2 按组织维度查询**
```
GET /api/v1/query/organization?deptName=xxx&userName=xxx&startDate=2024-01-01&endDate=2024-01-31&page=1&size=20
Authorization: Bearer {token}
```

**3.3 导出查询结果**
```
POST /api/v1/query/export
Authorization: Bearer {token}
Content-Type: application/json

{
  "queryType": "project",
  "filters": {
    "projectName": "xxx",
    "startDate": "2024-01-01",
    "endDate": "2024-01-31"
  }
}
```

#### 4. 工时核对 (4个)

**4.1 完整性检查**
```
POST /api/v1/check/integrity
Authorization: Bearer {token}
Content-Type: application/json

{
  "startDate": "2024-01-01",
  "endDate": "2024-01-31",
  "deptName": "技术部",
  "userName": "张三",
  "workdays": [1, 2, 3, 4, 5]
}

响应:
{
  "code": 200,
  "data": {
    "batchNo": "CHK_20240115103000_5678",
    "totalWorkdays": 22,
    "totalUsers": 10,
    "abnormalUsers": ["张三", "李四"],
    "totalMissingDays": 5,
    "integrityRate": "80.00%",
    "list": [...]
  }
}
```

**4.2 合规性检查**
```
POST /api/v1/check/compliance
Authorization: Bearer {token}
Content-Type: application/json

{
  "startDate": "2024-01-01",
  "endDate": "2024-01-31",
  "standardHours": 8,
  "minHours": 4,
  "maxOvertime": 4,
  "maxMonthlyOvertime": 80
}
```

**4.3 获取核对历史**
```
GET /api/v1/check/history?checkType=integrity&page=1&size=20
Authorization: Bearer {token}
```

**4.4 获取核对记录详情**
```
GET /api/v1/check/record/{batchNo}
Authorization: Bearer {token}
```

#### 5. 系统管理 (5个)

**5.1 获取系统配置**
```
GET /api/v1/system/config?category=import
Authorization: Bearer {token}
```

**5.2 更新系统配置**
```
PUT /api/v1/system/config
Authorization: Bearer {token}
Content-Type: application/json

{
  "configs": [
    {
      "configKey": "import.max_rows",
      "configValue": "1000"
    }
  ]
}
```

**5.3 备份数据库**
```
POST /api/v1/system/backup
Authorization: Bearer {token}
```

**5.4 恢复数据库**
```
POST /api/v1/system/restore
Authorization: Bearer {token}
Content-Type: application/json

{
  "filename": "backup_20240115_103000.db"
}
```

**5.5 获取备份列表**
```
GET /api/v1/system/backups
Authorization: Bearer {token}
```

**5.6 获取系统信息**
```
GET /api/v1/system/info
Authorization: Bearer {token}
```

## 数据导入格式说明

### Excel 文件格式要求

- **文件格式**: `.xlsx` 或 `.xls`
- **文件大小**: 最大 10MB
- **最大行数**: 1000 行

### 必填字段

| 字段名 | 说明 | 示例 |
|--------|------|------|
| 序号 | 审批单序号 | 202401150001 |
| 姓名 | 员工姓名 | 张三 |
| 开始时间 | 工作开始时间 | 2024-01-15 09:00:00 |
| 结束时间 | 工作结束时间 | 2024-01-15 18:00:00 |
| 项目名称 | 项目名称 | XX项目开发 |
| 审批结果 | 审批结果（仅支持"通过"） | 通过 |
| 审批状态 | 审批状态（仅支持"已完成"） | 已完成 |
| 项目交付-工作时长 | 工作时长（小时） | 8 |

### 可选字段

| 字段名 | 说明 | 示例 |
|--------|------|------|
| 项目经理 | 项目经理姓名 | 李经理 |
| 部门 | 部门名称 | 技术部 |
| 项目交付-加班时长 | 加班时长（小时） | 2 |

### 数据验证规则

1. **审批结果**: 必须为"通过"
2. **审批状态**: 必须为"已完成"
3. **工作时长**: 0-24 小时
4. **加班时长**: ≥0 小时
5. **唯一性标识**: 序号+姓名+开始时间+项目名称

## 配置说明

### 系统配置项

| 配置键 | 默认值 | 说明 | 可编辑 |
|--------|--------|------|--------|
| import.max_file_size | 10 | 单次导入最大文件大小(MB) | 是 |
| import.max_rows | 1000 | 单次导入最大行数 | 是 |
| import.duplicate_strategy | skip | 重复数据处理策略(skip/cover) | 是 |
| check.standard_hours | 8 | 标准工作时长(小时) | 是 |
| check.min_hours | 4 | 最小工作时长(小时) | 是 |
| check.max_overtime | 4 | 单日最大加班时长(小时) | 是 |
| check.max_monthly_overtime | 80 | 月度最大加班时长(小时) | 是 |
| check.workdays | [1,2,3,4,5] | 标准工作日(1-7) | 是 |

### 环境变量

创建 `.env` 文件并配置以下变量：

```bash
# JWT 密钥（生产环境必须修改）
JWT_SECRET_KEY=your-secret-key-change-in-production

# 数据库路径
DATABASE_PATH=instance/workinghour.db

# 上传文件大小限制 (MB)
MAX_CONTENT_LENGTH=10
```

## 生产环境部署

### 使用 Gunicorn

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

### 使用 systemd

创建 `/etc/systemd/system/workinghour.service`:

```ini
[Unit]
Description=Working Hour Backend Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/src/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start workinghour
sudo systemctl enable workinghour
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 开发指南

### 添加新的路由

1. 在 `app/routes/` 创建新的路由文件
2. 定义 Blueprint 并实现路由函数
3. 在 `app/__init__.py` 中注册 Blueprint

### 添加新的数据模型

1. 在 `app/models/` 创建新的模型文件
2. 继承 `db.Model`
3. 定义字段和方法
4. 运行应用时自动创建表

### 运行测试

```bash
# 运行所有测试
python -m pytest

# 运行指定测试文件
python -m pytest tests/test_auth.py
```

## 常见问题

### Q: 如何修改默认密码？

A: 登录后通过数据库直接修改，或在代码中修改 `_init_default_data()` 函数中的默认密码。

### Q: 如何清理临时上传文件？

A: 临时文件位于 `instance/uploads/`，可以定期手动清理或添加定时任务自动清理。

### Q: 数据库文件在哪里？

A: 开发环境位于 `instance/workinghour.db`，生产环境可通过 `DATABASE_PATH` 环境变量配置。

### Q: 如何迁移到 MySQL？

A: 修改 `config.py` 中的 `SQLALCHEMY_DATABASE_URI`：

```python
SQLALCHEMY_DATABASE_URI = 'mysql://user:password@localhost/workinghour'
```

## 许可证

本项目仅供内部使用。

## 联系方式

如有问题，请联系开发团队。
