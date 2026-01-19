#!/bin/bash

################################################################################
# 工时统计系统 - 一键部署脚本
# 功能：从 GitHub 拉取代码并自动部署前后端项目
# 使用方法：
#   首次部署： ./deploy.sh init
#   更新部署： ./deploy.sh update
#   回滚：     ./deploy.sh rollback [commit_hash]
################################################################################

set -e  # 遇到错误立即退出

# ==================== 配置区域 ====================

# GitHub 仓库地址（请修改为您的仓库地址）
GITHUB_REPO="https://github.com/yourusername/workinghour.git"

# 部署路径
DEPLOY_DIR="/var/www/workinghour"
FRONTEND_BUILD_DIR="$DEPLOY_DIR/frontend/dist"
BACKEND_DIR="$DEPLOY_DIR/backend"

# 服务配置
SERVICE_NAME="workinghour"
NGINX_SERVICE="nginx"

# Node.js 版本
NODE_VERSION="18"

# Python 虚拟环境路径
VENV_DIR="$DEPLOY_DIR/venv"

# 备份目录
BACKUP_DIR="$DEPLOY_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 日志文件
LOG_FILE="/var/log/workinghour/deploy.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==================== 工具函数 ====================

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        error "$1 未安装，请先安装后再执行部署"
    fi
}

# 检查并创建目录
ensure_dir() {
    if [ ! -d "$1" ]; then
        log "创建目录: $1"
        sudo mkdir -p "$1"
        sudo chown $USER:$USER "$1"
    fi
}

# ==================== 环境检查 ====================

check_environment() {
    log "检查系统环境..."

    # 检查必要命令
    check_command git
    check_command python3
    check_command npm

    # 检查是否为 root 用户
    if [ "$EUID" -eq 0 ]; then
        error "请不要使用 root 用户运行此脚本"
    fi

    # 检查 sudo 权限
    if ! sudo -n true 2>/dev/null; then
        log "需要 sudo 权限，请输入密码..."
        sudo true
    fi

    log "环境检查完成 ✓"
}

# ==================== 首次部署 ====================

init_deploy() {
    log "========== 开始首次部署 =========="

    # 1. 拉取代码
    if [ -d "$DEPLOY_DIR" ]; then
        warn "部署目录已存在，请先备份或删除"
        read -p "是否继续？(y/N): " confirm
        if [ "$confirm" != "y" ]; then
            error "部署已取消"
        fi
        sudo rm -rf "$DEPLOY_DIR"
    fi

    log "从 GitHub 拉取代码..."
    git clone "$GITHUB_REPO" "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"

    # 2. 设置后端环境
    log "配置后端环境..."
    cd "$DEPLOY_DIR/src/backend"

    # 创建 Python 虚拟环境
    log "创建 Python 虚拟环境..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"

    # 安装 Python 依赖
    log "安装 Python 依赖..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install gunicorn

    # 创建 .env 文件
    if [ ! -f .env ]; then
        log "创建后端环境配置文件..."
        cat > .env << EOF
# JWT 密钥（请务必修改）
JWT_SECRET_KEY=$(openssl rand -hex 32)
FLASK_SECRET_KEY=$(openssl rand -hex 32)

# 数据库路径
DATABASE_PATH=$DEPLOY_DIR/data/workinghour.db

# CORS 配置（请修改为您的域名）
ALLOWED_ORIGINS=http://localhost:8080

# 日志级别
LOG_LEVEL=INFO
EOF
        warn "请修改 .env 文件中的配置（JWT密钥、CORS域名等）"
    fi

    # 创建数据目录
    ensure_dir "$DEPLOY_DIR/data"
    ensure_dir "$BACKUP_DIR"

    # 初始化数据库
    log "初始化数据库..."
    python init_db.py

    # 3. 设置前端环境
    log "配置前端环境..."
    cd "$DEPLOY_DIR/src/frontend"

    # 安装 Node 依赖
    log "安装 Node.js 依赖..."
    npm install

    # 创建生产环境配置
    cat > .env.production << EOF
# 生产环境 API 地址（请修改为您的域名）
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
EOF
    warn "请修改 .env.production 文件中的 API 地址"

    # 构建前端
    log "构建前端..."
    npm run build

    # 4. 配置 Systemd 服务
    log "配置 Systemd 服务..."
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=Working Hour Statistics System
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$DEPLOY_DIR/src/backend
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 5. 配置 Nginx
    log "配置 Nginx..."
    sudo tee /etc/nginx/sites-available/$SERVICE_NAME > /dev/null << EOF
server {
    listen 80;
    server_name _;  # 请修改为您的域名

    # 前端静态文件
    root $FRONTEND_BUILD_DIR;
    index index.html;

    # 前端路由支持
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # API 反向代理到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # 文件上传大小限制
    client_max_body_size 10M;
}
EOF

    # 启用 Nginx 配置
    sudo ln -sf /etc/nginx/sites-available/$SERVICE_NAME /etc/nginx/sites-enabled/

    # 测试 Nginx 配置
    sudo nginx -t

    # 6. 启动服务
    log "启动服务..."
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl start $SERVICE_NAME
    sudo systemctl reload $NGINX_SERVICE

    # 7. 设置权限
    log "设置文件权限..."
    sudo chown -R $USER:$USER "$DEPLOY_DIR"
    sudo chmod -R 755 "$FRONTEND_BUILD_DIR"

    log "========== 部署完成 =========="
    echo ""
    echo "🎉 部署成功！"
    echo ""
    echo "后续步骤："
    echo "1. 修改后端配置: $DEPLOY_DIR/src/backend/.env"
    echo "2. 修改前端配置: $DEPLOY_DIR/src/frontend/.env.production"
    echo "3. 修改 Nginx 配置中的域名: /etc/nginx/sites-available/$SERVICE_NAME"
    echo "4. 配置 SSL 证书（推荐使用 Let's Encrypt）"
    echo "5. 重启服务: sudo systemctl restart $SERVICE_NAME"
    echo ""
    echo "常用命令："
    echo "- 查看后端日志: sudo journalctl -u $SERVICE_NAME -f"
    echo "- 重启后端: sudo systemctl restart $SERVICE_NAME"
    echo "- 重启 Nginx: sudo systemctl restart $NGINX_SERVICE"
    echo ""
}

# ==================== 更新部署 ====================

update_deploy() {
    log "========== 开始更新部署 =========="

    # 检查是否已部署
    if [ ! -d "$DEPLOY_DIR" ]; then
        error "未找到部署目录，请先运行首次部署: ./deploy.sh init"
    fi

    # 备份当前版本
    log "备份当前版本..."
    BACKUP_NAME="backup_$TIMESTAMP"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    mkdir -p "$BACKUP_PATH"

    # 备份数据库
    if [ -f "$DEPLOY_DIR/src/backend/.env" ]; then
        source "$DEPLOY_DIR/src/backend/.env"
        DB_PATH="${DATABASE_PATH:-$DEPLOY_DIR/data/workinghour.db}"
        if [ -f "$DB_PATH" ]; then
            cp "$DB_PATH" "$BACKUP_PATH/workinghour.db"
            log "数据库已备份到: $BACKUP_PATH/workinghour.db"
        fi
    fi

    # 备份配置文件
    [ -f "$DEPLOY_DIR/src/backend/.env" ] && cp "$DEPLOY_DIR/src/backend/.env" "$BACKUP_PATH/"
    [ -f "$DEPLOY_DIR/src/frontend/.env.production" ] && cp "$DEPLOY_DIR/src/frontend/.env.production" "$BACKUP_PATH/"

    # 拉取最新代码
    log "从 GitHub 拉取最新代码..."
    cd "$DEPLOY_DIR"
    git fetch origin
    CURRENT_COMMIT=$(git rev-parse HEAD)

    # 显示更新内容
    log "待更新的提交："
    git log HEAD..origin/main --oneline

    read -p "是否继续更新？(y/N): " confirm
    if [ "$confirm" != "y" ]; then
        log "更新已取消"
        exit 0
    fi

    git pull origin main

    # 更新后端
    log "更新后端..."
    cd "$DEPLOY_DIR/src/backend"
    source "$VENV_DIR/bin/activate"

    # 更新依赖
    pip install --upgrade pip
    pip install -r requirements.txt

    # 停止服务
    log "停止后端服务..."
    sudo systemctl stop $SERVICE_NAME

    # 数据库迁移（如果有新的数据库变更）
    # python migrate_db.py

    # 重启后端服务
    log "重启后端服务..."
    sudo systemctl start $SERVICE_NAME

    # 更新前端
    log "更新前端..."
    cd "$DEPLOY_DIR/src/frontend"

    # 安装新依赖
    npm install

    # 构建前端
    npm run build

    # 重启 Nginx
    log "重启 Nginx..."
    sudo systemctl reload $NGINX_SERVICE

    log "========== 更新完成 =========="
    log "备份已保存到: $BACKUP_PATH"

    # 检查服务状态
    sleep 3
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        log "✓ 后端服务运行正常"
    else
        error "✗ 后端服务启动失败，请检查日志: sudo journalctl -u $SERVICE_NAME"
    fi
}

# ==================== 回滚 ====================

rollback_deploy() {
    log "========== 开始回滚 =========="

    if [ -z "$1" ]; then
        error "请指定回滚到的 commit hash"
    fi

    COMMIT_HASH=$1

    # 检查是否已部署
    if [ ! -d "$DEPLOY_DIR" ]; then
        error "未找到部署目录"
    fi

    cd "$DEPLOY_DIR"

    # 创建回滚前的备份
    log "创建回滚前备份..."
    ROLLBACK_BACKUP="$BACKUP_DIR/before_rollback_$TIMESTAMP"
    mkdir -p "$ROLLBACK_BACKUP"

    if [ -f "$DEPLOY_DIR/src/backend/.env" ]; then
        source "$DEPLOY_DIR/src/backend/.env"
        DB_PATH="${DATABASE_PATH:-$DEPLOY_DIR/data/workinghour.db}"
        [ -f "$DB_PATH" ] && cp "$DB_PATH" "$ROLLBACK_BACKUP/"
    fi

    # 回滚代码
    log "回滚到 commit: $COMMIT_HASH"
    git checkout $COMMIT_HASH

    # 重新构建
    log "重新构建后端..."
    cd "$DEPLOY_DIR/src/backend"
    source "$VENV_DIR/bin/activate"
    pip install -r requirements.txt
    sudo systemctl restart $SERVICE_NAME

    log "重新构建前端..."
    cd "$DEPLOY_DIR/src/frontend"
    npm install
    npm run build
    sudo systemctl reload $NGINX_SERVICE

    log "========== 回滚完成 =========="
    log "回滚前备份已保存到: $ROLLBACK_BACKUP"
}

# ==================== 状态检查 ====================

check_status() {
    log "========== 系统状态 =========="

    echo ""
    echo "📁 部署目录: $DEPLOY_DIR"
    if [ -d "$DEPLOY_DIR" ]; then
        echo "   ✓ 目录存在"
        cd "$DEPLOY_DIR"
        echo "   当前分支: $(git branch --show-current)"
        echo "   当前提交: $(git rev-parse --short HEAD)"
        echo "   最后更新: $(git log -1 --format='%ci' HEAD)"
    else
        echo "   ✗ 目录不存在"
    fi

    echo ""
    echo "🔧 后端服务:"
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "   ✓ 运行中"
        echo "   PID: $(sudo systemctl show -p MainPID --value $SERVICE_NAME)"
    else
        echo "   ✗ 未运行"
    fi

    echo ""
    echo "🌐 Nginx 服务:"
    if systemctl is-active --quiet $NGINX_SERVICE; then
        echo "   ✓ 运行中"
    else
        echo "   ✗ 未运行"
    fi

    echo ""
    echo "💾 备份文件:"
    if [ -d "$BACKUP_DIR" ]; then
        BACKUP_COUNT=$(ls -1 "$BACKUP_DIR" | wc -l)
        echo "   共 $BACKUP_COUNT 个备份"
        if [ $BACKUP_COUNT -gt 0 ]; then
            echo "   最新备份:"
            ls -lt "$BACKUP_DIR" | head -6 | tail -5 | awk '{print "   " $NF}'
        fi
    else
        echo "   无备份目录"
    fi

    echo ""
}

# ==================== 主程序 ====================

main() {
    # 创建日志目录
    ensure_dir "$(dirname $LOG_FILE)"

    case "$1" in
        init)
            check_environment
            init_deploy
            ;;
        update)
            check_environment
            update_deploy
            ;;
        rollback)
            check_environment
            rollback_deploy "$2"
            ;;
        status)
            check_status
            ;;
        *)
            echo "工时统计系统 - 部署脚本"
            echo ""
            echo "使用方法："
            echo "  $0 init       - 首次部署"
            echo "  $0 update     - 更新部署"
            echo "  $0 rollback <commit> - 回滚到指定版本"
            echo "  $0 status     - 查看系统状态"
            echo ""
            echo "示例："
            echo "  $0 init"
            echo "  $0 update"
            echo "  $0 rollback abc123"
            echo "  $0 status"
            exit 1
            ;;
    esac
}

# 执行主程序
main "$@"
