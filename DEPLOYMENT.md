# 部署脚本使用说明

本目录包含两个自动化部署脚本，分别用于 Linux/Unix 和 Windows 系统。

## 📋 目录

- [Linux/macOS 部署 (deploy.sh)](#linuxmacos-部署-deploysh)
- [Windows 部署 (deploy.ps1)](#windows-部署-deployps1)
- [部署前准备](#部署前准备)
- [常见问题](#常见问题)

---

## Linux/macOS 部署 (deploy.sh)

### 使用前准备

1. **修改脚本中的配置**
   ```bash
   # 编辑 deploy.sh，修改以下变量：
   GITHUB_REPO="https://github.com/yourusername/workinghour.git"  # 改为你的仓库地址
   ```

2. **赋予执行权限**
   ```bash
   chmod +x deploy.sh
   ```

### 首次部署

```bash
./deploy.sh init
```

**脚本将自动完成：**
- ✅ 从 GitHub 拉取代码
- ✅ 创建 Python 虚拟环境并安装依赖
- ✅ 安装 Node.js 依赖并构建前端
- ✅ 创建并初始化 SQLite 数据库
- ✅ 配置 Systemd 服务
- ✅ 配置 Nginx 反向代理
- ✅ 启动所有服务

### 更新部署

```bash
./deploy.sh update
```

**脚本将自动完成：**
- ✅ 备份数据库和配置文件
- ✅ 拉取最新代码
- ✅ 更新 Python 和 Node.js 依赖
- ✅ 重新构建前后端
- ✅ 重启服务

### 回滚版本

```bash
# 查看提交历史
git log --oneline

# 回滚到指定版本
./deploy.sh rollback abc1234
```

### 查看系统状态

```bash
./deploy.sh status
```

### 常用运维命令

```bash
# 查看后端日志
sudo journalctl -u workinghour -f

# 重启后端服务
sudo systemctl restart workinghour

# 重启 Nginx
sudo systemctl restart nginx

# 查看服务状态
sudo systemctl status workinghour
```

---

## Windows 部署 (deploy.ps1)

### 使用前准备

1. **以管理员身份运行 PowerShell**
   - 右键点击 PowerShell 图标
   - 选择"以管理员身份运行"

2. **允许执行脚本**
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **修改脚本中的配置**
   ```powershell
   # 编辑 deploy.ps1，修改以下变量：
   $script:GITHUB_REPO = "https://github.com/yourusername/workinghour.git"
   ```

### 首次部署

```powershell
.\deploy.ps1 init
```

**脚本将自动完成：**
- ✅ 从 GitHub 拉取代码
- ✅ 创建 Python 虚拟环境并安装依赖
- ✅ 安装 Node.js 依赖并构建前端
- ✅ 创建并初始化 SQLite 数据库
- ✅ 创建 Windows 服务 (需要安装 NSSM)
- ✅ 配置 IIS 站点 (如果已安装)

### 更新部署

```powershell
.\deploy.ps1 update
```

### 回滚版本

```powershell
# 查看提交历史
git log --oneline

# 回滚到指定版本
.\deploy.ps1 rollback abc1234
```

### 查看系统状态

```powershell
.\deploy.ps1 status
```

### 常用运维命令

```powershell
# 查看服务状态
Get-Service WorkingHourBackend

# 启动服务
Start-Service WorkingHourBackend

# 停止服务
Stop-Service WorkingHourBackend

# 重启服务
Restart-Service WorkingHourBackend

# 查看事件日志
Get-EventLog -LogName Application -Source WorkingHourBackend -Newest 50
```

---

## 部署前准备

### Linux/macOS 系统要求

- **操作系统**: Ubuntu 20.04+ / Debian 10+ / CentOS 7+ / macOS 10.15+
- **Git**: 2.0+
- **Python**: 3.8+
- **Node.js**: 18+
- **Nginx**: 1.18+
- **Systemd**: 已启用

### Windows 系统要求

- **操作系统**: Windows 10/11 或 Windows Server 2016+
- **Git**: 2.0+
- **Python**: 3.8+
- **Node.js**: 18+
- **IIS**: 可选，用于托管前端
- **NSSM**: 可选，用于创建 Windows 服务

### 安装依赖 (Linux)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y git python3 python3-venv nodejs npm nginx

# CentOS/RHEL
sudo yum install -y git python3 python3-venv nodejs npm nginx

# macOS
brew install git python node nginx
```

### 安装依赖 (Windows)

1. **Git**: https://git-scm.com/download/win
2. **Python**: https://www.python.org/downloads/
3. **Node.js**: https://nodejs.org/
4. **IIS**: 通过"启用或关闭 Windows 功能"安装
5. **NSSM** (可选): https://nssm.cc/download

---

## 配置说明

### 后端配置 (.env)

首次部署后，需要修改以下配置：

```bash
# 编辑后端配置文件
cd /var/www/workinghour/src/backend  # Linux
# 或
cd C:\inetpub\workinghour\src\backend  # Windows

nano .env  # Linux
notepad .env  # Windows
```

**必须修改的配置：**

```env
# JWT 密钥（必须修改为强密钥）
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this

# Flask 密钥（必须修改）
FLASK_SECRET_KEY=your-flask-secret-key-change-this

# CORS 允许的域名（修改为你的前端域名）
ALLOWED_ORIGINS=https://yourdomain.com
```

### 前端配置 (.env.production)

```bash
# 编辑前端配置文件
cd /var/www/workinghour/src/frontend  # Linux
# 或
cd C:\inetpub\workinghour\src\frontend  # Windows

nano .env.production  # Linux
notepad .env.production  # Windows
```

**必须修改的配置：**

```env
# 后端 API 地址（修改为你的后端域名）
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
```

### Nginx 配置 (Linux)

```bash
# 编辑 Nginx 配置
sudo nano /etc/nginx/sites-available/workinghour
```

**修改服务器名称：**

```nginx
server {
    listen 80;
    server_name yourdomain.com;  # 修改为你的域名
    # ...
}
```

---

## SSL/HTTPS 配置

### Linux 使用 Let's Encrypt

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取并自动配置 SSL 证书
sudo certbot --nginx -d yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

### Windows IIS SSL

1. 获取 SSL 证书（如 Let's Encrypt 使用 win-acme）
2. 在 IIS 管理器中绑定证书
3. 配置 HTTP 到 HTTPS 重定向

---

## 常见问题

### 1. 权限错误

**Linux:**
```bash
sudo chown -R $USER:$USER /var/www/workinghour
```

**Windows:**
```powershell
# 以管理员身份运行 PowerShell
```

### 2. 端口被占用

**Linux:**
```bash
# 查看占用 8000 端口的进程
sudo lsof -i :8000

# 杀死进程
sudo kill -9 <PID>
```

**Windows:**
```powershell
# 查看占用 8000 端口的进程
netstat -ano | findstr :8000

# 杀死进程
taskkill /PID <PID> /F
```

### 3. 服务启动失败

**Linux:**
```bash
# 查看服务日志
sudo journalctl -u workinghour -n 50

# 检查配置
sudo systemctl status workinghour
```

**Windows:**
```powershell
# 查看事件日志
Get-EventLog -LogName Application -Newest 50 | Where-Object {$_.Source -like "*WorkingHour*"}
```

### 4. Git 仓库认证问题

如果使用私有仓库，需要配置 SSH 密钥或个人访问令牌：

```bash
# SSH 方式
GITHUB_REPO="git@github.com:yourusername/workinghour.git"

# HTTPS 方式（使用令牌）
GITHUB_REPO="https://YOUR_TOKEN@github.com/yourusername/workinghour.git"
```

### 5. 数据库连接错误

**检查数据库路径：**
```bash
# Linux
cat /var/www/workinghour/src/backend/.env | grep DATABASE_PATH

# Windows
Get-Content C:\inetpub\workinghour\src\backend\.env | Select-String DATABASE_PATH

# 确保目录存在且有写权限
mkdir -p /var/www/workinghour/data
chmod 755 /var/www/workinghour/data
```

### 6. 前端构建失败

```bash
# 清除缓存重新构建
cd src/frontend
rm -rf node_modules package-lock.json  # Linux
Remove-Item -Recurse -Force node_modules, package-lock.json  # Windows

npm install
npm run build
```

### 7. Python 依赖安装失败

```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 生产环境建议

### 1. 安全加固

- ✅ 修改所有默认密钥
- ✅ 配置防火墙规则
- ✅ 启用 HTTPS
- ✅ 定期更新系统和依赖
- ✅ 配置 fail2ban 防暴力破解

### 2. 数据备份

- ✅ 定期备份数据库（使用系统内置备份功能）
- ✅ 备份配置文件
- ✅ 将备份存储到远程位置

### 3. 监控和日志

- ✅ 配置日志轮转
- ✅ 监控磁盘空间
- ✅ 监控服务状态
- ✅ 配置告警通知

### 4. 性能优化

- ✅ 使用 Gunicorn 多worker
- ✅ 配置 Nginx 缓存
- ✅ 启用 gzip 压缩
- ✅ 使用 CDN 加速前端资源

---

## 目录结构

部署后的目录结构：

```
/var/www/workinghour/                    # 部署根目录
├── src/                                 # 源代码
│   ├── backend/                         # 后端代码
│   │   ├── app/                         # Flask 应用
│   │   ├── config.py                    # 配置文件
│   │   ├── requirements.txt             # Python 依赖
│   │   └── .env                         # 环境变量
│   └── frontend/                        # 前端代码
│       ├── src/                         # Vue 源码
│       ├── dist/                        # 构建产物
│       ├── package.json                 # Node 依赖
│       └── .env.production              # 生产环境配置
├── venv/                                # Python 虚拟环境
├── data/                                # 数据目录
│   └── workinghour.db                   # SQLite 数据库
└── backups/                             # 备份目录
    ├── backup_20240101_120000/
    └── backup_20240102_150000/
```

---

## 支持与反馈

如遇到问题，请检查：

1. ✅ 系统日志（journalctl 或事件查看器）
2. ✅ 应用日志
3. ✅ Nginx/IIS 日志
4. ✅ Git 仓库状态

需要帮助？请提交 Issue 到项目仓库。
