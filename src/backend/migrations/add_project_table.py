"""
添加项目表和工时数据外键字段

执行时间：2026-03-03
说明：
1. 创建 projects 表
2. 为 work_hour_data 表添加 project_id 外键字段
"""

import sqlite3
import os

def get_db_path():
    """获取数据库路径"""
    # Flask 默认使用 instance 目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'instance', 'workinghour.db')


def migrate():
    """执行迁移"""
    db_path = get_db_path()

    # 确保目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    print(f'数据库路径: {db_path}')

    if not os.path.exists(db_path):
        print(f'数据库文件不存在: {db_path}')
        print('请先启动应用创建数据库')
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查 projects 表是否已存在
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='projects'
        """)
        if cursor.fetchone():
            print('projects 表已存在，跳过创建')
        else:
            # 创建 projects 表
            print('创建 projects 表...')
            cursor.execute("""
                CREATE TABLE projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_code VARCHAR(20) NOT NULL UNIQUE,
                    project_name VARCHAR(100) NOT NULL,
                    project_type VARCHAR(20) NOT NULL,
                    project_prefix VARCHAR(1) NOT NULL,
                    project_manager VARCHAR(50),
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """)
            print('projects 表创建成功')

            # 创建索引
            print('创建 projects 表索引...')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_code ON projects(project_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(project_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_type ON projects(project_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_manager ON projects(project_manager)')
            print('projects 表索引创建成功')

        # 检查 work_hour_data 表是否已有 project_id 列
        cursor.execute('PRAGMA table_info(work_hour_data)')
        columns = [row[1] for row in cursor.fetchall()]

        if 'project_id' in columns:
            print('work_hour_data 表已有 project_id 列，跳过添加')
        else:
            # 添加 project_id 列
            print('为 work_hour_data 表添加 project_id 列...')
            cursor.execute('ALTER TABLE work_hour_data ADD COLUMN project_id INTEGER')
            print('project_id 列添加成功')

            # 创建索引
            print('创建 work_hour_data.project_id 索引...')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_hour_data_project_id ON work_hour_data(project_id)')
            print('索引创建成功')

        # 提交更改
        conn.commit()
        print('\n数据库迁移完成！')

        # 显示表结构
        print('\n=== projects 表结构 ===')
        cursor.execute('PRAGMA table_info(projects)')
        for row in cursor.fetchall():
            print(f'  {row[1]}: {row[2]}')

        print('\n=== work_hour_data 表新增字段 ===')
        cursor.execute('PRAGMA table_info(work_hour_data)')
        for row in cursor.fetchall():
            if row[1] == 'project_id':
                print(f'  {row[1]}: {row[2]}')

    except Exception as e:
        conn.rollback()
        print(f'\n迁移失败: {e}')
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
