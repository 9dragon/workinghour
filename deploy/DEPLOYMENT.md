# 部署文档

本文档说明如何使用 Docker Compose 在远程服务器上部署项目工时统计系统。

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [详细部署步骤](#详细部署步骤)
- [服务管理](#服务管理)
- [故障排查](#故障排查)
- [数据备份](#数据备份)

## 环境要求

### 服务器要求

- **操作系统**: Linux (推荐 Ubuntu 20.04+ / CentOS 7+)
- **内存**: 最小 2GB，推荐 4GB+
- **磁盘**: 最小 10GB 可用空间
- **CPU**: 最小 2 核

### 软件要求

- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### 端口要求

| 端口 | 用途 | 说明 |
|------|------|------|
| 80 | 前端服务 | HTTP 访问 |
| 8000 | 后端 API | 由 Docker 内部网络访问，无需开放 |

## 快速开始

```bash
# 1. 克隆代码
git clone <repository-url> workinghour
cd workinghour

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，修改密钥等配置

# 3. 启动服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps
```

访问 `http://<your-server-ip>` 即可使用系统。

## 详细部署步骤

### 1. 安装 Docker 和 Docker Compose

#### Ubuntu/Debian

```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户加入 docker 组（可选，避免每次 sudo）
sudo usermod -aG docker $USER
newgrp docker

# 安装 Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

#### CentOS/RHEL

```bash
# 安装 Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. 准备项目文件

```bash
# 克隆项目
git clone <repository-url> workinghour
cd workinghour

# 配置环境变量
cp .env.example .env
nano .env  # 或使用 vim 编辑
```

**重要配置项:**

```bash
# 必须修改的密钥（生成随机字符串）
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# 根据实际域名修改 CORS_ORIGINS
CORS_ORIGINS=http://your-domain.com,https://your-domain.com
```

### 3. 构建和启动服务

```bash
# 构建镜像
docker-compose build

# 启动服务（后台运行）
docker-compose up -d

# 查看启动日志
docker-compose logs -f

# 确认服务状态
docker-compose ps
```

### 4. 验证部署

```bash
# 检查前端健康状态
curl http://localhost/health

# 检查后端健康状态
curl http://localhost:8000/api/health

# 或者使用部署脚本
./deploy.sh health
```

## 服务管理

### 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 启动指定服务
docker-compose up -d backend
docker-compose up -d frontend
```

### 停止服务

```bash
# 停止所有服务
docker-compose stop

# 停止指定服务
docker-compose stop backend
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启指定服务
docker-compose restart backend
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看指定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 查看最近 100 行日志
docker-compose logs --tail=100 backend
```

### 更新服务

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 或者使用部署脚本
./deploy.sh update
```

### 清理服务

```bash
# 停止并删除容器
docker-compose down

# 删除容器和数据卷（谨慎操作！）
docker-compose down -v

# 清理未使用的镜像
docker image prune -a
```

## 故障排查

### 服务无法启动

```bash
# 查看详细日志
docker-compose logs backend
docker-compose logs frontend

# 检查容器状态
docker-compose ps

# 进入容器调试
docker-compose exec backend /bin/bash
docker-compose exec frontend /bin/sh
```

### 端口冲突

如果 80 端口被占用，修改 `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "8080:80"  # 使用 8080 端口
```

### 数据库问题

```bash
# 检查数据库文件
docker-compose exec backend ls -lh /app/instance/

# 重置数据库（危险操作！）
docker-compose down -v
docker-compose up -d
```

### 健康检查失败

```bash
# 查看健康检查状态
docker inspect --format='{{.State.Health.Status}}' workinghour-backend
docker inspect --format='{{.State.Health.Status}}' workinghour-frontend
```

### 内存不足

```bash
# 限制容器内存使用（在 docker-compose.yml 中添加）
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
```

## 数据备份

### 备份数据库

```bash
# 创建备份目录
mkdir -p backups

# 备份数据库
docker-compose exec backend cp /app/instance/workinghour.db /app/backups/workinghour_$(date +%Y%m%d_%H%M%S).db

# 从容器复制到主机
docker cp workinghour-backend:/app/backups ./backups/
```

### 恢复数据库

```bash
# 停止服务
docker-compose stop backend

# 复制备份文件到容器
docker cp backups/workinghour_20250122_120000.db workinghour-backend:/app/instance/workinghour.db

# 启动服务
docker-compose start backend
```

### 定期备份（使用 cron）

```bash
# 编辑 crontab
crontab -e

# 添加每日备份任务（每天凌晨 2 点）
0 2 * * * cd /path/to/workinghour && ./deploy.sh backup
```

## 生产环境建议

### 1. 配置 HTTPS

使用 Nginx 反向代理 + Let's Encrypt:

```bash
# 安装 certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 2. 配置防火墙

```bash
# Ubuntu UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable

# CentOS firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 3. 监控和日志

- 使用 Docker 日志驱动: `--log-driver=json-file --log-opt max-size=10m`
- 配置日志轮转: `--log-opt max-file=3`
- 考虑使用 ELK/Loki 等日志聚合方案

### 4. 资源限制

在 `docker-compose.yml` 中添加资源限制:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## 文件结构

```
workinghour/
├── docker-compose.yml          # Docker Compose 配置
├── .env.example                # 环境变量模板
├── .env                        # 环境变量（需创建）
├── deploy.sh                   # 部署脚本
├── src/
│   ├── backend/
│   │   ├── Dockerfile          # 后端镜像构建文件
│   │   ├── .dockerignore       # 后端构建忽略文件
│   │   ├── requirements.txt    # Python 依赖
│   │   └── app/                # 应用代码
│   └── frontend/
│       ├── Dockerfile          # 前端镜像构建文件
│       ├── .dockerignore       # 前端构建忽略文件
│       ├── nginx.conf          # Nginx 配置
│       └── src/                # 源代码
└── backups/                    # 备份目录（需创建）
```
