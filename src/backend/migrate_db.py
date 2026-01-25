"""
数据库迁移脚本 - 移除sys_users表中的real_name和dept_name字段
"""
import sqlite3
import os

db_path = 'instance/workinghour.db'

if not os.path.exists(db_path):
    print("数据库文件不存在，将在启动时自动创建")
    exit(0)

print("开始迁移数据库...")

# 备份数据库
backup_path = 'instance/workinghour_backup.db'
import shutil
shutil.copy2(db_path, backup_path)
print(f"已创建数据库备份: {backup_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取当前sys_users表的数据
    cursor.execute("SELECT * FROM sys_users")
    users = cursor.fetchall()

    # 获取列信息
    cursor.execute("PRAGMA table_info(sys_users)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    print(f"当前sys_users表字段: {column_names}")

    # 检查是否需要迁移
    if 'real_name' in column_names or 'dept_name' in column_names:
        print("\n需要移除字段: real_name, dept_name")

        # 创建新的sys_users表（不包含real_name和dept_name）
        cursor.execute("""
            CREATE TABLE sys_users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'user',
                email VARCHAR(100),
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                login_fail_count INTEGER NOT NULL DEFAULT 0,
                lock_time DATETIME,
                last_login_time DATETIME,
                last_login_ip VARCHAR(50),
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)

        # 复制数据（跳过real_name和dept_name列）
        if users:
            # 构建插入语句，排除real_name和dept_name
            insert_cols = [col for col in column_names if col not in ['real_name', 'dept_name', 'id']]
            col_indices = {col: i for i, col in enumerate(column_names)}

            for user in users:
                values = []
                for col in insert_cols:
                    idx = column_names.index(col)
                    values.append(user[idx])

                # 添加ID
                user_id = user[column_names.index('id')]
                values.insert(0, user_id)

                placeholders = ', '.join(['?' for _ in values])
                cursor.execute(f"INSERT INTO sys_users_new (id, {', '.join(insert_cols)}) VALUES ({placeholders})", values)

        # 删除旧表
        cursor.execute("DROP TABLE sys_users")

        # 重命名新表
        cursor.execute("ALTER TABLE sys_users_new RENAME TO sys_users")

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_sys_users_user_name ON sys_users (user_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_sys_users_status ON sys_users (status)")

        conn.commit()

        print("\n迁移成功！新的sys_users表结构：")
        cursor.execute("PRAGMA table_info(sys_users)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")

        # 验证employees表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
        if not cursor.fetchone():
            print("\n创建employees表...")
            cursor.execute("""
                CREATE TABLE employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_name VARCHAR(50) UNIQUE NOT NULL,
                    dept_name VARCHAR(50) NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX ix_employees_employee_name ON employees (employee_name)")
            cursor.execute("CREATE INDEX ix_employees_dept_name ON employees (dept_name)")
            conn.commit()
            print("employees表创建成功！")
        else:
            print("\nemployees表已存在")

        conn.close()
        print("\n数据库迁移完成！")
    else:
        print("sys_users表已经是最新结构，无需迁移")

        # 确保employees表存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
        if not cursor.fetchone():
            print("\n创建employees表...")
            cursor.execute("""
                CREATE TABLE employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_name VARCHAR(50) UNIQUE NOT NULL,
                    dept_name VARCHAR(50) NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX ix_employees_employee_name ON employees (employee_name)")
            cursor.execute("CREATE INDEX ix_employees_dept_name ON employees (dept_name)")
            conn.commit()
            print("employees表创建成功！")

        conn.close()
        print("\n数据库迁移完成！")

except Exception as e:
    print(f"\n迁移失败: {e}")
    print(f"备份文件保存在: {backup_path}")
    # 恢复备份
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, db_path)
        print("已从备份恢复数据库")
    exit(1)
