"""
数据库迁移脚本：修改 check_records 表的 start_date 和 end_date 字段允许为 NULL

执行方式：python -m migrations.alter_check_records_dates_nullable
"""
import sqlite3
import os
from datetime import datetime


def migrate():
    """执行迁移"""
    # 获取数据库路径
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'workinghour.db')

    if not os.path.exists(db_path):
        print(f"错误：数据库文件不存在: {db_path}")
        return False

    # 备份数据库
    backup_path = f"backups/backup_before_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)

    print(f"备份数据库到: {backup_path}")
    import shutil
    shutil.copy2(db_path, backup_path)
    print("备份完成")

    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("开始迁移...")

        # SQLite 不支持直接修改列的约束，需要重建表
        # 1. 创建新表
        cursor.execute('''
            CREATE TABLE check_records_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_no VARCHAR(50) UNIQUE NOT NULL,
                check_type VARCHAR(20) NOT NULL,
                start_date DATE,
                end_date DATE,
                dept_name VARCHAR(50),
                user_name VARCHAR(50),
                check_config TEXT NOT NULL,
                check_result TEXT NOT NULL,
                trigger_type VARCHAR(20) NOT NULL DEFAULT 'manual',
                check_user VARCHAR(50) NOT NULL,
                check_time DATETIME NOT NULL,
                report_path VARCHAR(255),
                created_at DATETIME NOT NULL
            )
        ''')

        # 2. 复制数据（显式指定字段名）
        cursor.execute('''
            INSERT INTO check_records_new (
                id, check_no, check_type, start_date, end_date,
                dept_name, user_name, check_config, check_result,
                trigger_type, check_user, check_time, report_path, created_at
            )
            SELECT
                id, check_no, check_type, start_date, end_date,
                dept_name, user_name, check_config, check_result,
                trigger_type, check_user, check_time, report_path, created_at
            FROM check_records
        ''')

        copied_rows = cursor.rowcount
        print(f"已复制 {copied_rows} 条记录")

        # 3. 删除旧表
        cursor.execute('DROP TABLE check_records')

        # 4. 重命名新表
        cursor.execute('ALTER TABLE check_records_new RENAME TO check_records')

        # 5. 重建索引
        cursor.execute('CREATE INDEX ix_check_records_check_no ON check_records (check_no)')
        cursor.execute('CREATE INDEX ix_check_records_check_type ON check_records (check_type)')
        cursor.execute('CREATE INDEX ix_check_records_dept_name ON check_records (dept_name)')
        cursor.execute('CREATE INDEX ix_check_records_user_name ON check_records (user_name)')
        cursor.execute('CREATE INDEX ix_check_records_check_time ON check_records (check_time)')

        # 提交更改
        conn.commit()

        print("迁移成功完成！")
        print("[OK] check_records.start_date 现在允许为 NULL")
        print("[OK] check_records.end_date 现在允许为 NULL")

        return True

    except Exception as e:
        # 发生错误，回滚
        conn.rollback()
        print(f"迁移失败: {str(e)}")
        print("正在恢复备份...")

        # 恢复备份
        conn.close()
        shutil.copy2(backup_path, db_path)
        print("已恢复到迁移前的状态")

        return False

    finally:
        conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("数据库迁移：修改 check_records 表日期字段可空性")
    print("=" * 60)
    print()

    success = migrate()

    print()
    print("=" * 60)
    if success:
        print("迁移成功！请重启应用。")
    else:
        print("迁移失败！请检查错误信息。")
    print("=" * 60)
