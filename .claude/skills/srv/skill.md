# srv - 服务管理 Skill

## 名称
`srv` - 工时统计系统前后端服务管理

## 描述
统一管理工时统计系统的前后端服务，支持启动、停止、重启和状态查看操作。

## 使用方法

### 基本命令
- `/srv` - 启动前后端服务
- `/srv start` - 启动前后端服务
- `/srv status` - 查看服务运行状态
- `/srv restart` - 重启前后端服务
- `/srv stop` - 停止前后端服务

### 功能说明

#### 启动服务 (`start`)
- 检查服务是否已运行（端口 + 进程名）
- 如果已运行，提示用户使用 `/srv restart`
- 启动后端：`cd src/backend && python run.py`（端口 8000）
- 启动前端：`cd src/frontend && npm run dev`（端口 3000）
- 显示启动状态和访问地址

#### 查看状态 (`status`)
显示服务状态表格：
```
┌─────────┬────────┬──────┬─────────┐
│ 服务    │ 状态   │ 端口 │ PID     │
├─────────┼────────┼──────┼─────────┤
│ 后端API │ 运行中 │ 8000 │ 12345   │
│ 前端Web │ 运行中 │ 3000 │ 67890   │
└─────────┴────────┴──────┴─────────┘
```

#### 重启服务 (`restart`)
- 停止现有服务（优雅关闭）
- 等待端口释放
- 重新启动服务
- 显示新服务状态

#### 停止服务 (`stop`)
- 查找并停止相关进程
- 确认端口已释放
- 显示停止结果

## 调用方式

通过 PowerShell 直接调用脚本文件（而非在 Bash 中嵌入命令）：

```powershell
# 查看状态
powershell -ExecutionPolicy Bypass -File ".claude\skills\srv\srv.ps1" status

# 启动服务
powershell -ExecutionPolicy Bypass -File ".claude\skills\srv\srv.ps1" start

# 停止服务
powershell -ExecutionPolicy Bypass -File ".claude\skills\srv\srv.ps1" stop

# 重启服务
powershell -ExecutionPolicy Bypass -File ".claude\skills\srv\srv.ps1" restart

# 显示帮助
powershell -ExecutionPolicy Bypass -File ".claude\skills\srv\srv.ps1" help
```

## 技术实现
- **端口检测**: 使用 `netstat` 命令（兼容性更好）
- **进程管理**: 使用 `taskkill /F` 强制终止
- **后台启动**: 使用 `Start-Process -WindowStyle Hidden`
- **执行方式**: PowerShell 脚本文件独立执行
- **操作系统**: Windows PowerShell 5.1+

## 服务配置
- **后端服务**:
  - 端口: 8000
  - 启动命令: `python src/backend/run.py`
  - 进程名: python

- **前端服务**:
  - 端口: 3000
  - 启动命令: `npm run dev` (在 src/frontend 目录)
  - 进程名: node

## 访问地址
- 前端: http://localhost:3000
- 后端: http://127.0.0.1:8000
- API 文档: http://127.0.0.1:8000/docs

## 注意事项
1. 需要已安装 Python 3.8+ 和 Node.js 16+
2. 首次启动前需要安装依赖：
   - 后端: `pip install -r src/backend/requirements.txt`
   - 前端: `cd src/frontend && npm install`
3. 端口 8000 和 3000 需要未被占用
4. 停止服务会终止所有相关进程，请确保已保存工作
