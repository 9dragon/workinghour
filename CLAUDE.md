# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

这是一个**项目工时统计 Web 应用** - 轻量级 Web 系统，用于统计和分析钉钉 OA 审批记录中的工时数据。用户从钉钉导出 Excel 文件后上传至系统，完成数据导入、查询和统计分析。

**当前状态：** 仅处于文档和设计阶段 - 尚未实现任何源代码。

## 计划技术栈

**前端：**
- Vue.js 3 + Vite
- Element Plus（UI 组件库）
- Axios（HTTP 客户端）
- Pinia（状态管理）

**后端：**
- Python Flask（REST API）
- SQLite 3（数据存储）
- pandas + openpyxl/xlsxwriter（Excel 处理）
- pydantic（数据校验）
- PyJWT（认证令牌）
- bcrypt（密码加密）

## 项目结构

```
workinghour/
├── requirements/          # 需求文档和原型
│   ├── 需求规格书.md      # 完整的产品需求规格说明书
│   ├── 示例数据-工时日志.xlsx  # 钉钉导出示例数据
│   └── prototype/         # AI 生成的前端原型
│       ├── frontend/      # 原型代码（待填充）
│       └── README.md      # 原型使用指南
├── design/               # 设计文档
│   ├── README.md         # 设计文档结构指南
│   └── 架构设计说明书.md  # 系统架构和技术设计
└── src/                  # 源代码（待实现）
```

## 核心架构模式

### 三层架构

1. **前端层：** 使用 Element Plus 组件的 Vue.js 单页应用
2. **后端层：** Flask REST API 服务器
3. **数据层：** SQLite 数据库（三个核心表）

### 核心业务模块

- **数据导入：** Excel 上传，多阶段校验（格式、字段、状态、唯一性）
- **工时查询：** 双维度查询（项目维度 + 组织维度）
- **用户认证：** 基于 JWT，包含账号锁定保护
- **数据导出：** 查询结果导出为 Excel 文件
- **导入记录：** 历史导入批次追踪

## 关键业务规则

### 数据导入约束

- **仅接受：** 审批结果为"通过"且审批状态为"已完成"的记录
- **唯一性标识：** `序号 + 姓名 + 开始时间 + 项目名称`
- **文件限制：** 最大 10MB，单次导入最多 1000 行
- **支持格式：** .xls 和 .xlsx
- **重复数据处理：** 默认"跳过重复数据"，可选"覆盖重复数据"

### 查询功能

- **项目维度：** 按项目名称、项目经理、时间范围筛选
- **组织维度：** 按部门名称、姓名、时间范围筛选
- **结果展示：** 15 个数据字段，分页显示（20/50/100 行每页）
- **导出：** Excel 文件名格式为 `工时查询结果_{查询维度}_{查询时间}`

### 数据库表结构

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `work_hour_data` | 工时数据主表 | id, serial_no, user_name, start_time, end_time, project_name, work_hours, overtime_hours, dept_name, import_batch_no |
| `import_records` | 导入批次追踪表 | batch_no, file_name, total_rows, success_rows, repeat_rows, invalid_rows |
| `sys_users` | 用户认证表 | user_name, password (bcrypt), login_fail_count, lock_time |

## 开发命令（计划）

```bash
# 前端开发
cd src/frontend
npm install
npm run dev          # 启动开发服务器
npm run build        # 生产环境构建

# 后端开发
cd src/backend
pip install -r requirements.txt
python app.py        # 启动开发服务器

# 生产环境部署
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 性能要求

- 页面加载：≤ 2 秒
- Excel 导入（1000 行）：≤ 30 秒
- 查询响应：≤ 3 秒（单条件），≤ 5 秒（多条件组合）
- 并发用户数：最多 50 人

## 安全要求

- 登录失败 5 次后锁定账号 30 分钟
- 密码使用 bcrypt 加密存储
- 不对接钉钉 API（仅支持手动上传 Excel）
- 文件上传校验，防止恶意文件
- 基于 JWT 令牌的身份认证

## 重要设计决策

1. **不集成钉钉 API：** 由于成本限制，系统仅接受从钉钉手动导出的 Excel 文件
2. **单数据库部署：** 选择 SQLite 以简化部署，未来可低成本迁移至 MySQL
3. **文件存储方式：** 临时文件存储在本地文件系统，自动清理（保留 7 天）
4. **极简中间件：** 不使用消息队列或复杂分布式组件 - 简化单机部署

## AI 代码生成策略

本项目设计为 AI 友好型。使用 AI 生成代码时：

1. **前端：** 充分利用 Element Plus 组件（表格、表单、上传、弹窗）- AI 可生成清晰标准的代码
2. **后端：** 使用 Flask 标准模式 - AI 能很好地处理路由、校验和数据库操作
3. **Excel 处理：** pandas + pydantic 组合 - AI 对这两个库有深入理解
4. **原型：** 在 `requirements/prototype/frontend/` 生成前端原型，作为实现参考（不可直接复制）

## 参考文档

- **需求规格：** `requirements/需求规格书.md` - 完整的功能和非功能需求
- **架构设计：** `design/架构设计说明书.md` - 技术选型、模块结构、数据模型设计
- **原型指南：** `requirements/prototype/README.md` - 开发过程中如何使用 AI 生成的原型
