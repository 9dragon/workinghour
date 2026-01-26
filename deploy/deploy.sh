#!/bin/bash
#
# 部署脚本 - 项目工时统计系统
# 用法: ./deploy.sh [command]
#

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
}

# 检查环境变量文件
check_env() {
    if [ ! -f ../.env ]; then
        log_warn ".env 文件不存在，从 .env.example 复制"
        cp ../.env.example ../.env
        log_warn "请编辑 .env 文件，设置正确的配置后重新运行"
        exit 1
    fi
}

# Docker Compose 命令兼容
docker_compose() {
    if docker compose version &> /dev/null 2>&1; then
        docker compose "$@"
    else
        docker-compose "$@"
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
部署脚本 - 项目工时统计系统

用法: ./deploy.sh [command]

命令:
    build       构建 Docker 镜像
    up          启动服务（后台运行）
    down        停止并删除容器
    restart     重启服务
    logs        查看服务日志
    status      查看服务状态
    health      健康检查
    update      更新服务（拉取代码并重新构建）
    backup      备份数据库
    restore     恢复数据库
    clean       清理未使用的镜像和容器
    prune       完全清理（包括数据卷）

示例:
    ./deploy.sh build          # 构建镜像
    ./deploy.sh up             # 启动服务
    ./deploy.sh logs           # 查看日志
    ./deploy.sh update         # 更新服务

EOF
}

# 构建镜像
build() {
    log_info "开始构建 Docker 镜像..."
    check_env
    docker_compose build --no-cache
    log_info "镜像构建完成"
}

# 启动服务
up() {
    log_info "启动服务..."
    check_env
    docker_compose up -d
    log_info "服务启动完成"
    log_info "前端访问地址: http://localhost"
    log_info "后端 API 地址: http://localhost:8000/api"
}

# 停止服务
down() {
    log_info "停止服务..."
    docker_compose down
    log_info "服务已停止"
}

# 重启服务
restart() {
    log_info "重启服务..."
    docker_compose restart
    log_info "服务已重启"
}

# 查看日志
logs() {
    check_env
    if [ -n "$1" ]; then
        docker_compose logs -f "$1"
    else
        docker_compose logs -f
    fi
}

# 查看状态
status() {
    log_info "服务状态:"
    docker_compose ps
}

# 健康检查
health() {
    log_info "执行健康检查..."

    # 检查前端
    if curl -sf http://localhost/health > /dev/null 2>&1; then
        log_info "前端服务: 正常"
    else
        log_error "前端服务: 异常"
    fi

    # 检查后端
    if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
        log_info "后端服务: 正常"
    else
        log_error "后端服务: 异常"
    fi
}

# 更新服务
update() {
    log_info "更新服务..."

    # 拉取最新代码
    if [ -d ../.git ]; then
        log_info "拉取最新代码..."
        (cd .. && git pull)
    fi

    # 重新构建并启动
    docker_compose up -d --build

    log_info "服务更新完成"
}

# 备份数据库
backup() {
    log_info "备份数据库..."

    # 创建备份目录
    mkdir -p ../backups

    # 备份文件名
    backup_file="workinghour_$(date +%Y%m%d_%H%M%S).db"

    # 从容器复制数据库
    if docker_compose exec -T backend cp /app/instance/workinghour.db "/app/backups/$backup_file" 2>/dev/null; then
        docker cp "workinghour-backend:/app/backups/$backup_file" "../backups/$backup_file"
        log_info "数据库已备份到: ../backups/$backup_file"
    else
        log_error "数据库备份失败"
    fi
}

# 恢复数据库
restore() {
    if [ -z "$1" ]; then
        log_error "请指定备份文件路径"
        echo "用法: ./deploy.sh restore <backup-file>"
        exit 1
    fi

    backup_file="$1"

    if [ ! -f "$backup_file" ]; then
        log_error "备份文件不存在: $backup_file"
        exit 1
    fi

    log_warn "即将恢复数据库，现有数据将被覆盖！"
    read -p "确认继续? (y/N) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "停止后端服务..."
        docker_compose stop backend

        log_info "恢复数据库: $backup_file"
        docker cp "$backup_file" workinghour-backend:/app/instance/workinghour.db

        log_info "启动后端服务..."
        docker_compose start backend

        log_info "数据库恢复完成"
    else
        log_info "已取消"
    fi
}

# 清理未使用的资源
clean() {
    log_info "清理未使用的镜像和容器..."
    docker system prune -f
    log_info "清理完成"
}

# 完全清理
prune() {
    log_warn "此操作将删除所有容器、镜像、数据卷！"
    read -p "确认继续? (y/N) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "停止并删除所有容器..."
        docker_compose down -v

        log_info "删除所有未使用的资源..."
        docker system prune -a --volumes -f

        log_info "清理完成"
    else
        log_info "已取消"
    fi
}

# 主函数
main() {
    check_docker

    case "${1:-}" in
        build)
            build
            ;;
        up)
            up
            ;;
        down)
            down
            ;;
        restart)
            restart
            ;;
        logs)
            logs "${2:-}"
            ;;
        status)
            status
            ;;
        health)
            health
            ;;
        update)
            update
            ;;
        backup)
            backup
            ;;
        restore)
            restore "${2:-}"
            ;;
        clean)
            clean
            ;;
        prune)
            prune
            ;;
        *)
            show_help
            ;;
    esac
}

main "$@"
