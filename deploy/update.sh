# Git 操作在项目根目录执行
(cd .. && git stash)
(cd .. && git pull --rebase)
(cd .. && git stash pop)

# Docker 操作在 deploy 目录执行
docker-compose build
docker-compose down
docker-compose up -d
