"""
修改 project_budgets 表，添加项目关联

执行时间：2026-03-03
说明：
1. 添加 project_code 字段用于与 projects 表关联
2. 保留 project_name 字段用于兼容性
3. 将现有数据的 project_name 提取项目代码并填充到 project_code
"""

import sqlite3
import os
import re

def get_db_path():
    """获取数据库路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    return os.path.join(backend_dir, 'instance', 'workinghour.db')


def extract_project_code(project_name):
    """从项目名称中提取项目代码"""
    if not project_name:
        return None
    # 匹配 D 或 P 开头的数字编号
    match = re.match(r'^([DP]\d+)', project_name)
    if match:
        return match.group(1)
    return None


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
        # 检查字段是否已存在
        cursor.execute('PRAGMA table_info(project_budgets)')
        columns = [row[1] for row in cursor.fetchall()]

        if 'project_code' in columns:
            print('project_code 字段已存在，跳过迁移')
            # 显示当前数据
            cursor.execute('SELECT project_name, project_code FROM project_budgets LIMIT 5')
            print('\n当前预算记录示例:')
            for row in cursor.fetchall():
                print(f'  {row[0]} -> {row[1]}')
            return

        # 1. 添加 project_code 字段
        print('添加 project_code 字段...')
        cursor.execute('ALTER TABLE project_budgets ADD COLUMN project_code VARCHAR(20)')

        # 2. 更新现有数据，提取项目代码
        print('更新现有数据，提取项目代码...')
        cursor.execute('SELECT id, project_name FROM project_budgets')
        rows = cursor.fetchall()

        updated_count = 0
        for row_id, project_name in rows:
            project_code = extract_project_code(project_name)
            if project_code:
                cursor.execute(
                    'UPDATE project_budgets SET project_code = ? WHERE id = ?',
                    (project_code, row_id)
                )
                updated_count += 1

        print(f'已更新 {updated_count} 条记录')

        # 3. 创建索引
        print('创建索引...')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_budgets_project_code ON project_budgets(project_code)')

        # 提交更改
        conn.commit()
        print('\n数据库迁移完成！')

        # 显示结果
        print('\n=== 更新后的数据示例 ===')
        cursor.execute('SELECT project_name, project_code FROM project_budgets LIMIT 10')
        for row in cursor.fetchall():
            print(f'  {row[0]} -> {row[1]}')

    except Exception as e:
        conn.rollback()
        print(f'\n迁移失败: {e}')
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
