"""
数据库迁移脚本：添加 check_details 字段到 check_records 表

执行方式：python -m migrations.add_check_details_column
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
    backup_path = f"backups/backup_before_add_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
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

        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(check_records)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'check_details' in columns:
            print("check_details 列已存在，跳过迁移")
            return True

        # 添加 check_details 列
        cursor.execute('''
            ALTER TABLE check_records ADD COLUMN check_details TEXT
        ''')

        print("已添加 check_details 列")

        # 验证列是否添加成功
        cursor.execute("PRAGMA table_info(check_records)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'check_details' in columns:
            print("验证成功：check_details 列已存在")
        else:
            raise Exception("列添加失败")

        # 提交更改
        conn.commit()

        print("迁移成功完成！")
        print("[OK] check_records.check_details 字段已添加")
        print("    该字段允许为 NULL，兼容现有记录")

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
    print("数据库迁移：添加 check_details 字段")
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
