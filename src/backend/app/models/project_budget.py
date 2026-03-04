"""
项目工时预算表
"""
from datetime import datetime
from .db import db

class ProjectBudget(db.Model):
    """项目工时预算表"""
    __tablename__ = 'project_budgets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_name = db.Column(db.String(100), nullable=False, index=True)  # 保留用于显示
    project_code = db.Column(db.String(20), nullable=False, index=True)  # 关联 projects 表
    budget_type = db.Column(db.String(20), nullable=False)  # 预算类型：project_manager/data_collection/software_dev
    budget_hours = db.Column(db.Numeric(10, 2), nullable=False, default=0)  # 预算工时，单位：人天
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 唯一约束：同一项目、同一类型只能有一条预算记录
    __table_args__ = (
        db.UniqueConstraint('project_code', 'budget_type', name='uix_project_type'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'projectName': self.project_name,
            'projectCode': self.project_code,
            'budgetType': self.budget_type,
            'budgetTypeLabel': self.get_budget_type_label(),
            'budgetHours': float(self.budget_hours) if self.budget_hours else 0,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

    def get_budget_type_label(self):
        """获取预算类型标签"""
        type_labels = {
            'project_manager': '项目管理',
            'data_collection': '数采实施',
            'software_dev': '软件实施'
        }
        return type_labels.get(self.budget_type, '未知')
