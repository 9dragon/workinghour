"""
重建数据库脚本
"""
import os
import sys

# 删除旧数据库
db_path = 'instance/workinghour.db'
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print(f"已删除旧数据库: {db_path}")
    except Exception as e:
        print(f"删除数据库失败: {e}")
        sys.exit(1)

# 创建新数据库
from app import create_app
from app.models.db import db

app = create_app()
with app.app_context():
    db.create_all()
    print("数据库表创建成功！")

    # 验证表结构
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n当前数据库中的表：")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")

    print("\nemployees表结构：")
    cursor.execute('PRAGMA table_info(employees)')
    for col in cursor.fetchall():
        print(f"  {col[1]} ({col[2]})")

    print("\nsys_users表结构：")
    cursor.execute('PRAGMA table_info(sys_users)')
    cols = cursor.fetchall()
    for col in cols:
        print(f"  {col[1]} ({col[2]})")

    # 检查是否还有real_name和dept_name字段
    user_fields = [col[1] for col in cols]
    if 'real_name' in user_fields or 'dept_name' in user_fields:
        print("\n警告：sys_users表仍然包含旧字段！")
        print("请检查app/models/user.py是否已正确修改")
    else:
        print("\n✓ sys_users表结构正确（已移除real_name和dept_name）")

    conn.close()

print("\n数据库重建完成！")
