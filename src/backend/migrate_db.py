"""
数据库迁移脚本（命令行入口）。

迁移逻辑实现在 app/migrations.py，应用启动时也会自动调用 run_migrations()。
本脚本仅用于手动运维场景（带备份、详细输出）。

用法：
    python migrate_db.py
"""
from app.migrations import run_migrations
from config import Config


if __name__ == '__main__':
    print("开始迁移数据库...")
    run_migrations(
        db_path=Config.DATABASE_PATH,
        backup=True,
        verbose=True,
    )
    print("\n迁移流程结束")
