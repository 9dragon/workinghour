"""
重命名 project_budgets 表的 role 字段为 budget_type

执行时间：2026-03-03
说明：
1. 将 role 字段重命名为 budget_type
2. 更新唯一约束名称
"""

import sqlite3
import os

def get_db_path():
    """获取数据库路径"""
    # 从当前 migrations 目录向上两级到 backend 目录，然后找 instance 目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    return os.path.join(backend_dir, 'instance', 'workinghour.db')


def migrate():
    """执行迁移"""
    db_path = get_db_path()

    if not os.path.exists(db_path):
        print(f'数据库文件不存在: {db_path}')
        return

    print(f'数据库路径: {db_path}')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # SQLite 不支持直接重命名列，需要重建表
        print('开始重命名 project_budgets 表的 role 字段为 budget_type...')

        # 1. 检查字段是否已存在
        cursor.execute('PRAGMA table_info(project_budgets)')
        columns = [row[1] for row in cursor.fetchall()]

        if 'budget_type' in columns:
            print('budget_type 字段已存在，跳过迁移')
            return

        if 'role' not in columns:
            print('role 字段不存在，无需迁移')
            return

        # 2. 创建新表
        print('创建新表结构...')
        cursor.execute("""
            CREATE TABLE project_budgets_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name VARCHAR(100) NOT NULL,
                budget_type VARCHAR(20) NOT NULL,
                budget_hours NUMERIC(10, 2) NOT NULL DEFAULT 0,
                fiscal_year VARCHAR(10) NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                UNIQUE(project_name, budget_type, fiscal_year)
            )
        """)

        # 3. 复制数据
        print('复制数据到新表...')
        cursor.execute("""
            INSERT INTO project_budgets_new
            SELECT id, project_name, role, budget_hours, fiscal_year, created_at, updated_at
            FROM project_budgets
        """)
        rows_copied = cursor.rowcount
        print(f'已复制 {rows_copied} 行数据')

        # 4. 删除旧表
        print('删除旧表...')
        cursor.execute('DROP TABLE project_budgets')

        # 5. 重命名新表
        print('重命名新表...')
        cursor.execute('ALTER TABLE project_budgets_new RENAME TO project_budgets')

        # 6. 重建索引
        print('重建索引...')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_budgets_project_name ON project_budgets(project_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_budgets_fiscal_year ON project_budgets(fiscal_year)')

        # 提交更改
        conn.commit()
        print('\n数据库迁移完成！')

        # 显示新表结构
        print('\n=== project_budgets 表结构 ===')
        cursor.execute('PRAGMA table_info(project_budgets)')
        for row in cursor.fetchall():
            print(f'  {row[1]}: {row[2]}')

    except Exception as e:
        conn.rollback()
        print(f'\n迁移失败: {e}')
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
