# 工时统计系统

一个轻量级的 Web 应用，用于统计和分析钉钉 OA 审批记录中的工时数据。

## 项目简介

本项目用于企业内部工时管理，支持从钉钉导出的 Excel 文件导入、数据查询统计、工时核对等功能。系统采用前后端分离架构，部署简单，易于维护。

> **当前状态**：处于设计阶段，原型已完成，源代码待实现。

## 功能特性

| 模块 | 功能 | 说明 |
|------|------|------|
| **数据导入** | Excel 文件上传 | 支持拖拽上传，多阶段数据校验 |
| | 重复数据处理 | 跳过或覆盖重复数据 |
| | 导入记录追踪 | 历史批次查询，导入报告导出 |
| **工时查询** | 项目维度查询 | 按项目/经理/时间筛选 |
| | 组织维度查询 | 按部门/人员/时间筛选 |
| | 结果导出 | 支持查询结果导出 Excel |
| **工时核对** | 完整性检查 | 检查缺失工时记录 |
| | 合规性检查 | 检查异常工时数据 |
| | 核对历史记录 | 历史核对记录查询 |
| **系统管理** | 用户认证 | JWT 令牌，账号锁定保护 |
| | 数据备份恢复 | 系统数据备份与恢复 |
| | 系统配置 | 系统参数配置管理 |

## 技术栈

### 前端
- **框架**：Vue.js 3 (Composition API)
- **构建工具**：Vite 4.x
- **UI 组件库**：Element Plus 2.4.x
- **状态管理**：Pinia
- **HTTP 客户端**：Axios
- **日期处理**：Day.js

### 后端
- **框架**：Python Flask
- **数据库**：SQLite 3
- **Excel 处理**：pandas + openpyxl
- **数据校验**：pydantic
- **认证**：PyJWT + bcrypt

## 目录结构

```
workinghour/
├── README.md                  # 项目说明（本文档）
├── CLAUDE.md                  # Claude Code 开发指南
├── requirements/              # 需求文档
│   ├── 需求规格书.md          # 完整的产品需求规格说明书
│   ├── 示例数据-工时日志.xlsx # 钉钉导出示例数据
│   └── prototype/             # 前端原型
│       ├── frontend/          # Vue.js 原型代码
│       └── README.md          # 原型使用指南
├── design/                    # 设计文档
│   ├── README.md              # 设计文档导航
│   └── 架构设计说明书.md      # 系统架构和技术设计
└── src/                       # 源代码（待实现）
    ├── frontend/              # 前端代码
    └── backend/               # 后端代码
```

## 环境要求

### Node.js 版本管理

本项目使用 Node.js 18 LTS，如需与其他项目共存，推荐使用 **nvm-windows** 管理多版本：

```bash
# 安装 nvm-windows (如未安装)
# 下载地址: https://github.com/coreybutler/nvm-windows/releases

# 安装 Node.js 18
nvm install 18.20.3
nvm use 18.20.3

# 切换到其他版本（如 Node 14）
nvm use 14.21.3
```

### 系统要求

| 组件 | 版本要求 |
|------|----------|
| Node.js | >= 18.x (推荐 18.20.3 LTS) |
| npm | >= 9.x |
| Python | >= 3.9 |
| 浏览器 | Chrome/Edge/Firefox (最新版) |

## 快速开始

### 1. 查看前端原型（含模拟登录）

```bash
# 切换到 Node.js 18
nvm use 18.20.3

# 安装依赖
cd requirements/prototype/frontend
npm install

# 启动开发服务器
npm run dev
```

访问 `http://localhost:3000` 查看原型效果。

#### 模拟登录

前端原型已启用**模拟模式**，无需后端即可体验完整功能：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | 任意（≥6位） | 管理员 |
| user | 任意（≥6位） | 普通用户 |
| 其他任意用户名 | 任意（≥6位） | 普通用户 |

**模拟功能**：
- 用户登录
- Excel 数据导入（模拟数据）
- 工时查询（项目维度/组织维度）
- 工时核对（完整性/合规性）
- 导入记录查询
- 系统设置（备份/恢复）

> **注意**：模拟模式下所有数据均为演示数据，不会真正存储。关闭模拟模式需修改 `src/utils/request.js` 中的 `MOCK_MODE = false`。

### 2. 后端开发（待实现）

```bash
cd src/backend
pip install -r requirements.txt
python app.py
```

### 3. 前端开发（待实现）

```bash
cd src/frontend
npm install
npm run dev
```

### 4. 生产构建

```bash
# 前端构建
cd src/frontend
npm run build

# 后端部署
cd src/backend
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 开发指南

### 开发流程

1. **阅读文档**：了解需求和架构设计
2. **查看原型**：运行原型，理解交互逻辑
3. **实现后端**：按照架构设计实现 API
4. **实现前端**：参考原型实现页面和交互
5. **联调测试**：前后端联调，功能测试

### 文档导航

| 文档 | 路径 | 说明 |
|------|------|------|
| 需求规格书 | [requirements/需求规格书.md](requirements/需求规格书.md) | 完整的功能和非功能需求 |
| 架构设计 | [design/架构设计说明书.md](design/架构设计说明书.md) | 技术选型、架构模式、数据模型 |
| 原型指南 | [requirements/prototype/README.md](requirements/prototype/README.md) | 原型使用和开发参考 |
| 开发指南 | [CLAUDE.md](CLAUDE.md) | Claude Code 辅助开发指南 |

### 核心业务规则

**数据导入约束**
- 仅接受审批结果为"通过"且审批状态为"已完成"的记录
- 唯一性标识：`序号 + 姓名 + 开始时间 + 项目名称`
- 文件限制：最大 10MB，单次最多 1000 行
- 支持格式：.xls 和 .xlsx

**性能要求**
- 页面加载：≤ 2 秒
- Excel 导入（1000 行）：≤ 30 秒
- 查询响应：≤ 3 秒（单条件），≤ 5 秒（多条件）
- 并发用户数：最多 50 人

## 开源协议

MIT License

## 更新日志

### v0.1.1 (2026-01-15)
- 添加前端模拟登录功能
- 更新文档，补充模拟模式使用说明

### v0.1.0 (2026-01-15)
- 完成需求分析和架构设计
- 完成前端原型开发
- 环境配置完成（Node.js 18 + 前端依赖）
