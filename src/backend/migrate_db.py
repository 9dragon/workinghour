"""
数据库迁移脚本

迁移项（幂等，可重复执行）：
1. sys_users 表移除 real_name / dept_name 字段（旧版遗留）
2. 创建 employees 表（若不存在）
3. employees 表增加 phone、email 列（用于通知）
"""
import sqlite3
import os
import shutil

db_path = 'instance/workinghour.db'

if not os.path.exists(db_path):
    print("数据库文件不存在，将在启动时自动创建")
    exit(0)

print("开始迁移数据库...")

backup_path = 'instance/workinghour_backup.db'
shutil.copy2(db_path, backup_path)
print(f"已创建数据库备份: {backup_path}")


def table_exists(cursor, name):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cursor.fetchone() is not None


def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def migrate_sys_users(cursor):
    if not table_exists(cursor, 'sys_users'):
        return
    cursor.execute("PRAGMA table_info(sys_users)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'real_name' not in cols and 'dept_name' not in cols:
        print("sys_users 表已是最新结构，无需迁移")
        return

    print("需要从 sys_users 移除 real_name、dept_name 字段")
    cursor.execute("SELECT * FROM sys_users")
    users = cursor.fetchall()
    keep_cols = [c for c in cols if c not in ('real_name', 'dept_name')]
    col_idx = {c: i for i, c in enumerate(cols)}

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

    for user in users:
        values = [user[col_idx[c]] for c in keep_cols]
        placeholders = ', '.join(['?'] * len(values))
        cursor.execute(
            f"INSERT INTO sys_users_new ({', '.join(keep_cols)}) VALUES ({placeholders})",
            values
        )

    cursor.execute("DROP TABLE sys_users")
    cursor.execute("ALTER TABLE sys_users_new RENAME TO sys_users")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_sys_users_user_name ON sys_users (user_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_sys_users_status ON sys_users (status)")
    print("sys_users 表迁移完成")


def ensure_employees_table(cursor):
    if table_exists(cursor, 'employees'):
        return
    print("创建 employees 表")
    cursor.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name VARCHAR(50) UNIQUE NOT NULL,
            dept_name VARCHAR(50) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'staff',
            phone VARCHAR(20),
            email VARCHAR(100),
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_employees_employee_name ON employees (employee_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_employees_dept_name ON employees (dept_name)")
    print("employees 表创建完成")


def ensure_employees_columns(cursor):
    """幂等加列 phone、email（SQLite ALTER TABLE ADD COLUMN，无 IF NOT EXISTS 语法）"""
    if not column_exists(cursor, 'employees', 'phone'):
        cursor.execute("ALTER TABLE employees ADD COLUMN phone VARCHAR(20)")
        print("employees 表新增 phone 列")
    if not column_exists(cursor, 'employees', 'email'):
        cursor.execute("ALTER TABLE employees ADD COLUMN email VARCHAR(100)")
        print("employees 表新增 email 列")


def ensure_employees_role(cursor):
    """老 employees 表可能没有 role 列"""
    if not column_exists(cursor, 'employees', 'role'):
        cursor.execute("ALTER TABLE employees ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'staff'")
        print("employees 表新增 role 列")


def ensure_notification_logs_table(cursor):
    """创建 notification_logs 表（幂等）"""
    if table_exists(cursor, 'notification_logs'):
        return
    print("创建 notification_logs 表")
    cursor.execute("""
        CREATE TABLE notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_no VARCHAR(50),
            employee_name VARCHAR(50),
            dept_name VARCHAR(50),
            channel VARCHAR(20),
            status VARCHAR(20),
            error_message TEXT,
            sent_at DATETIME NOT NULL,
            created_at DATETIME NOT NULL
        )
    """)
    for col in ('check_no', 'employee_name', 'channel', 'status', 'sent_at'):
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS ix_notification_logs_{col} ON notification_logs ({col})"
        )
    print("notification_logs 表创建完成")


def ensure_notification_logs_content_column(cursor):
    """幂等加 content 列（存储实际发送的消息体）"""
    if not column_exists(cursor, 'notification_logs', 'content'):
        cursor.execute("ALTER TABLE notification_logs ADD COLUMN content TEXT")
        print("notification_logs 表新增 content 列")


try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    migrate_sys_users(cursor)
    ensure_employees_table(cursor)
    ensure_employees_role(cursor)
    ensure_employees_columns(cursor)
    ensure_notification_logs_table(cursor)
    ensure_notification_logs_content_column(cursor)

    conn.commit()
    conn.close()
    print("\n数据库迁移完成！")

except Exception as e:
    print(f"\n迁移失败: {e}")
    print(f"备份文件保存在: {backup_path}")
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, db_path)
        print("已从备份恢复数据库")
    exit(1)
