"""
员工信息表
"""
from datetime import datetime
from .db import db

class Employee(db.Model):
    """员工信息表（仅存储姓名和部门，不包含登录信息）"""
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    dept_name = db.Column(db.String(50), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'employeeName': self.employee_name,
            'deptName': self.dept_name,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }
