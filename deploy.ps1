################################################################################
# 工时统计系统 - 一键部署脚本 (Windows PowerShell 版本)
# 功能：从 GitHub 拉取代码并自动部署前后端项目
# 使用方法：
#   首次部署： .\deploy.ps1 init
#   更新部署： .\deploy.ps1 update
#   回滚：     .\deploy.ps1 rollback <commit_hash>
################################################################################

param(
    [Parameter(Position=0)]
    [ValidateSet("init", "update", "rollback", "status", "help")]
    [string]$Command = "help",

    [Parameter(Position=1)]
    [string]$CommitHash = ""
)

# ==================== 配置区域 ====================

# GitHub 仓库地址（请修改为您的仓库地址）
$script:GITHUB_REPO = "https://github.com/yourusername/workinghour.git"

# 部署路径
$script:DEPLOY_DIR = "C:\inetpub\workinghour"
$script:FRONTEND_BUILD_DIR = "$DEPLOY_DIR\frontend\dist"
$script:BACKEND_DIR = "$DEPLOY_DIR\backend"

# 服务名称
$script:SERVICE_NAME = "WorkingHourBackend"

# Python 虚拟环境路径
$script:VENV_DIR = "$DEPLOY_DIR\venv"

# 备份目录
$script:BACKUP_DIR = "$DEPLOY_DIR\backups"
$script:TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"

# 日志文件
$script:LOG_FILE = "C:\Logs\workinghour\deploy.log"

# ==================== 工具函数 ====================

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor Green
    Add-Content -Path $LOG_FILE -Value $logMessage -ErrorAction SilentlyContinue
}

function Write-ErrorLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[ERROR] $Message"
    Write-Host $logMessage -ForegroundColor Red
    Add-Content -Path $LOG_FILE -Value $logMessage -ErrorAction SilentlyContinue
    throw $logMessage
}

function Write-WarnLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[WARN] $Message"
    Write-Host $logMessage -ForegroundColor Yellow
    Add-Content -Path $LOG_FILE -Value $logMessage -ErrorAction SilentlyContinue
}

function Test-Command {
    param([string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    return $null -ne $command
}

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        Write-Log "创建目录: $Path"
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

# ==================== 环境检查 ====================

function Test-Environment {
    Write-Log "检查系统环境..."

    # 检查必要命令
    if (-not (Test-Command git)) {
        Write-ErrorLog "Git 未安装，请先安装 Git for Windows"
    }
    Write-Log "✓ Git 已安装"

    if (-not (Test-Command python)) {
        Write-ErrorLog "Python 未安装，请先安装 Python 3.8+"
    }
    Write-Log "✓ Python 已安装"

    if (-not (Test-Command npm)) {
        Write-ErrorLog "Node.js 未安装，请先安装 Node.js 18+"
    }
    Write-Log "✓ Node.js 已安装"

    # 检查管理员权限
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-ErrorLog "请以管理员身份运行此脚本（右键 - 以管理员身份运行）"
    }
    Write-Log "✓ 管理员权限确认"

    Write-Log "环境检查完成"
}

# ==================== 首次部署 ====================

function Initialize-Deployment {
    Write-Log "========== 开始首次部署 =========="

    # 1. 拉取代码
    if (Test-Path $DEPLOY_DIR) {
        Write-WarnLog "部署目录已存在: $DEPLOY_DIR"
        $confirm = Read-Host "是否继续？将删除现有目录 (y/N)"
        if ($confirm -ne "y") {
            Write-ErrorLog "部署已取消"
        }
        Remove-Item -Path $DEPLOY_DIR -Recurse -Force
    }

    Write-Log "从 GitHub 拉取代码..."
    git clone $GITHUB_REPO $DEPLOY_DIR
    Set-Location $DEPLOY_DIR

    # 2. 设置后端环境
    Write-Log "配置后端环境..."
    Set-Location "$DEPLOY_DIR\src\backend"

    # 创建 Python 虚拟环境
    Write-Log "创建 Python 虚拟环境..."
    python -m venv $VENV_DIR
    & "$VENV_DIR\Scripts\Activate.ps1"

    # 安装 Python 依赖
    Write-Log "安装 Python 依赖..."
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    python -m pip install gunicorn waitress

    # 创建 .env 文件
    if (-not (Test-Path .env)) {
        Write-Log "创建后端环境配置文件..."
        $jwtSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
        $flaskSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})

        @"
# JWT 密钥（请务必修改）
JWT_SECRET_KEY=$jwtSecret
FLASK_SECRET_KEY=$flaskSecret

# 数据库路径
DATABASE_PATH=$DEPLOY_DIR\data\workinghour.db

# CORS 配置（请修改为您的域名）
ALLOWED_ORIGINS=http://localhost:8080

# 日志级别
LOG_LEVEL=INFO
"@ | Out-File -FilePath .env -Encoding UTF8

        Write-WarnLog "请修改 .env 文件中的配置（JWT密钥、CORS域名等）"
    }

    # 创建数据目录
    Ensure-Dir "$DEPLOY_DIR\data"
    Ensure-Dir $BACKUP_DIR

    # 初始化数据库
    Write-Log "初始化数据库..."
    python init_db.py

    # 3. 设置前端环境
    Write-Log "配置前端环境..."
    Set-Location "$DEPLOY_DIR\src\frontend"

    # 安装 Node 依赖
    Write-Log "安装 Node.js 依赖..."
    npm install

    # 创建生产环境配置
    @"
# 生产环境 API 地址（请修改为您的域名）
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
"@ | Out-File -FilePath .env.production -Encoding UTF8

    Write-WarnLog "请修改 .env.production 文件中的 API 地址"

    # 构建前端
    Write-Log "构建前端..."
    npm run build

    # 4. 创建 Windows 服务
    Write-Log "创建 Windows 服务..."

    # 使用 NSSM (Non-Sucking Service Manager) 创建服务
    $nsssPath = "nssm.exe"
    if (Test-Command nssm) {
        & $nsssPath install $SERVICE_NAME "$VENV_DIR\Scripts\python.exe" "$DEPLOY_DIR\src\backend\app.py"
        & $nsssPath set $SERVICE_NAME AppDirectory "$DEPLOY_DIR\src\backend"
        & $nsssPath set $SERVICE_NAME DisplayName "Working Hour Backend Service"
        & $nsssPath set $SERVICE_NAME Description "工时统计系统后端服务"
        & $nsssPath set $SERVICE_NAME Start SERVICE_AUTO_START
        Write-Log "✓ Windows 服务已创建"
    } else {
        Write-WarnLog "未找到 NSSM，请手动安装: https://nssm.cc/download"
        Write-WarnLog "或使用以下命令创建服务："
        Write-Host "sc create $SERVICE_NAME binPath= `"$VENV_DIR\Scripts\python.exe $DEPLOY_DIR\src\backend\app.py`"" -ForegroundColor Yellow
    }

    # 5. 配置 IIS (如果安装)
    $iisInstalled = Get-WindowsFeature -Name Web-Server -ErrorAction SilentlyContinue
    if ($iisInstalled -and $iisInstalled.InstallState -eq "Installed") {
        Write-Log "检测到 IIS，配置 IIS 站点..."

        # 导入 WebAdministration 模块
        Import-Module WebAdministration

        # 创建网站
        $siteName = "WorkingHour"
        $appPoolName = "WorkingHourPool"

        # 创建应用程序池
        if (-not (Test-Path "IIS:\AppPools\$appPoolName")) {
            New-WebAppPool -Name $appPoolName -Force
            Set-ItemProperty "IIS:\AppPools\$appPoolName" -Name "managedRuntimeVersion" -Value ""
        }

        # 创建网站
        if (-not (Get-Website -Name $siteName -ErrorAction SilentlyContinue)) {
            New-Website -Name $siteName -PhysicalPath $FRONTEND_BUILD_DIR -ApplicationPool $appPoolName -Port 80
        }

        # 配置反向代理（需要安装 ARR 和 URL Rewrite 模块）
        Write-WarnLog "如需 API 反向代理，请安装 IIS ARR 和 URL Rewrite 模块"

        Write-Log "✓ IIS 配置完成"
    } else {
        Write-WarnLog "未检测到 IIS，请手动配置 Web 服务器"
    }

    Write-Log "========== 部署完成 =========="
    Write-Host ""
    Write-Host "🎉 部署成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "后续步骤："
    Write-Host "1. 修改后端配置: $DEPLOY_DIR\src\backend\.env"
    Write-Host "2. 修改前端配置: $DEPLOY_DIR\src\frontend\.env.production"
    Write-Host "3. 启动服务: Start-Service $SERVICE_NAME"
    Write-Host "4. 配置防火墙规则"
    Write-Host "5. 配置 SSL 证书"
    Write-Host ""
    Write-Host "常用命令："
    Write-Host "- 查看服务状态: Get-Service $SERVICE_NAME"
    Write-Host "- 启动服务: Start-Service $SERVICE_NAME"
    Write-Host "- 停止服务: Stop-Service $SERVICE_NAME"
    Write-Host "- 重启服务: Restart-Service $SERVICE_NAME"
    Write-Host "- 查看日志: Get-EventLog -LogName Application -Source $SERVICE_NAME"
    Write-Host ""
}

# ==================== 更新部署 ====================

function Update-Deployment {
    Write-Log "========== 开始更新部署 =========="

    # 检查是否已部署
    if (-not (Test-Path $DEPLOY_DIR)) {
        Write-ErrorLog "未找到部署目录，请先运行首次部署: .\deploy.ps1 init"
    }

    # 备份当前版本
    Write-Log "备份当前版本..."
    $backupName = "backup_$TIMESTAMP"
    $backupPath = "$BACKUP_DIR\$backupName"
    New-Item -ItemType Directory -Path $backupPath -Force | Out-Null

    # 备份数据库
    $envFile = "$DEPLOY_DIR\src\backend\.env"
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match "DATABASE_PATH=(.+)") {
                $dbPath = $matches[1]
                if (Test-Path $dbPath) {
                    Copy-Item $dbPath "$backupPath\workinghour.db"
                    Write-Log "数据库已备份到: $backupPath\workinghour.db"
                }
            }
        }
    }

    # 备份配置文件
    if (Test-Path $envFile) { Copy-Item $envFile $backupPath\ }
    $frontendEnv = "$DEPLOY_DIR\src\frontend\.env.production"
    if (Test-Path $frontendEnv) { Copy-Item $frontendEnv $backupPath\ }

    # 拉取最新代码
    Write-Log "从 GitHub 拉取最新代码..."
    Set-Location $DEPLOY_DIR
    git fetch origin
    $currentCommit = git rev-parse HEAD

    # 显示更新内容
    Write-Log "待更新的提交："
    git log HEAD..origin/main --oneline

    $confirm = Read-Host "是否继续更新？(y/N)"
    if ($confirm -ne "y") {
        Write-Log "更新已取消"
        return
    }

    git pull origin main

    # 更新后端
    Write-Log "更新后端..."
    Set-Location "$DEPLOY_DIR\src\backend"
    & "$VENV_DIR\Scripts\Activate.ps1"

    # 更新依赖
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

    # 停止服务
    Write-Log "停止后端服务..."
    Stop-Service $SERVICE_NAME -Force

    # 重启后端服务
    Write-Log "重启后端服务..."
    Start-Service $SERVICE_NAME

    # 更新前端
    Write-Log "更新前端..."
    Set-Location "$DEPLOY_DIR\src\frontend"

    # 安装新依赖
    npm install

    # 构建前端
    npm run build

    # 重启 IIS (如果使用)
    $iisService = Get-Service -Name W3SVC -ErrorAction SilentlyContinue
    if ($iisService -and $iisService.Status -eq "Running") {
        Write-Log "重启 IIS..."
        Restart-Service W3SVC
    }

    Write-Log "========== 更新完成 =========="
    Write-Log "备份已保存到: $backupPath"

    # 检查服务状态
    Start-Sleep -Seconds 3
    $serviceStatus = Get-Service $SERVICE_NAME -ErrorAction SilentlyContinue
    if ($serviceStatus -and $serviceStatus.Status -eq "Running") {
        Write-Log "✓ 后端服务运行正常"
    } else {
        Write-ErrorLog "✗ 后端服务启动失败"
    }
}

# ==================== 回滚 ====================

function Invoke-Rollback {
    param([string]$CommitHash)

    Write-Log "========== 开始回滚 =========="

    if ([string]::IsNullOrEmpty($CommitHash)) {
        Write-ErrorLog "请指定回滚到的 commit hash"
    }

    # 检查是否已部署
    if (-not (Test-Path $DEPLOY_DIR)) {
        Write-ErrorLog "未找到部署目录"
    }

    Set-Location $DEPLOY_DIR

    # 创建回滚前的备份
    Write-Log "创建回滚前备份..."
    $rollbackBackup = "$BACKUP_DIR\before_rollback_$TIMESTAMP"
    New-Item -ItemType Directory -Path $rollbackBackup -Force | Out-Null

    $envFile = "$DEPLOY_DIR\src\backend\.env"
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match "DATABASE_PATH=(.+)") {
                $dbPath = $matches[1]
                if (Test-Path $dbPath) {
                    Copy-Item $dbPath "$rollbackBackup\"
                }
            }
        }
    }

    # 回滚代码
    Write-Log "回滚到 commit: $CommitHash"
    git checkout $CommitHash

    # 重新构建
    Write-Log "重新构建后端..."
    Set-Location "$DEPLOY_DIR\src\backend"
    & "$VENV_DIR\Scripts\Activate.ps1"
    python -m pip install -r requirements.txt
    Restart-Service $SERVICE_NAME

    Write-Log "重新构建前端..."
    Set-Location "$DEPLOY_DIR\src\frontend"
    npm install
    npm run build

    $iisService = Get-Service -Name W3SVC -ErrorAction SilentlyContinue
    if ($iisService -and $iisService.Status -eq "Running") {
        Restart-Service W3SVC
    }

    Write-Log "========== 回滚完成 =========="
    Write-Log "回滚前备份已保存到: $rollbackBackup"
}

# ==================== 状态检查 ====================

function Show-Status {
    Write-Log "========== 系统状态 =========="

    Write-Host ""
    Write-Host "📁 部署目录: $DEPLOY_DIR"
    if (Test-Path $DEPLOY_DIR) {
        Write-Host "   ✓ 目录存在" -ForegroundColor Green
        Set-Location $DEPLOY_DIR
        $branch = git branch --show-current
        $commit = git rev-parse --short HEAD
        $lastUpdate = git log -1 --format='%ci' HEAD
        Write-Host "   当前分支: $branch"
        Write-Host "   当前提交: $commit"
        Write-Host "   最后更新: $lastUpdate"
    } else {
        Write-Host "   ✗ 目录不存在" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "🔧 后端服务:"
    $serviceStatus = Get-Service $SERVICE_NAME -ErrorAction SilentlyContinue
    if ($serviceStatus) {
        if ($serviceStatus.Status -eq "Running") {
            Write-Host "   ✓ 运行中" -ForegroundColor Green
        } else {
            Write-Host "   ✗ 未运行 ($($serviceStatus.Status))" -ForegroundColor Red
        }
    } else {
        Write-Host "   ✗ 服务未创建" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "🌐 IIS 服务:"
    $iisStatus = Get-Service -Name W3SVC -ErrorAction SilentlyContinue
    if ($iisStatus -and $iisStatus.Status -eq "Running") {
        Write-Host "   ✓ 运行中" -ForegroundColor Green
    } else {
        Write-Host "   ✗ 未运行或未安装" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "💾 备份文件:"
    if (Test-Path $BACKUP_DIR) {
        $backups = Get-ChildItem $BACKUP_DIR | Measure-Object
        Write-Host "   共 $($backups.Count) 个备份"
        if ($backups.Count -gt 0) {
            Write-Host "   最新备份:"
            Get-ChildItem $BACKUP_DIR | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | ForEach-Object {
                Write-Host "   $($_.Name)"
            }
        }
    } else {
        Write-Host "   无备份目录" -ForegroundColor Yellow
    }

    Write-Host ""
}

# ==================== 主程序 ====================

function Main {
    # 创建日志目录
    Ensure-Dir (Split-Path $LOG_FILE -Parent)

    switch ($Command) {
        "init" {
            Test-Environment
            Initialize-Deployment
        }
        "update" {
            Test-Environment
            Update-Deployment
        }
        "rollback" {
            Test-Environment
            Invoke-Rollback -CommitHash $CommitHash
        }
        "status" {
            Show-Status
        }
        "help" {
            Write-Host "工时统计系统 - 部署脚本 (Windows PowerShell)" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "使用方法："
            Write-Host "  .\deploy.ps1 init              - 首次部署"
            Write-Host "  .\deploy.ps1 update            - 更新部署"
            Write-Host "  .\deploy.ps1 rollback <commit> - 回滚到指定版本"
            Write-Host "  .\deploy.ps1 status            - 查看系统状态"
            Write-Host ""
            Write-Host "示例："
            Write-Host "  .\deploy.ps1 init"
            Write-Host "  .\deploy.ps1 update"
            Write-Host "  .\deploy.ps1 rollback abc123"
            Write-Host "  .\deploy.ps1 status"
            Write-Host ""
            Write-Host "注意：请以管理员身份运行此脚本"
        }
    }
}

# 执行主程序
Main
