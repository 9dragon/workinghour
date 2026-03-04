"""
项目主表
"""
from datetime import datetime
from .db import db

class Project(db.Model):
    """项目主表"""
    __tablename__ = 'projects'

    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # 项目标识
    project_code = db.Column(db.String(20), unique=True, nullable=False, index=True)  # D4086, P1234
    project_name = db.Column(db.String(100), nullable=False, index=True)  # 完整名称

    # 项目分类
    project_type = db.Column(db.String(20), nullable=False, index=True)  # delivery/research/other
    project_prefix = db.Column(db.String(1), nullable=False)  # D/P/O

    # 项目管理
    project_manager = db.Column(db.String(50), index=True)
    status = db.Column(db.String(20), nullable=False, default='active')  # active/completed/suspended

    # 审计字段
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'projectCode': self.project_code,
            'projectName': self.project_name,
            'projectType': self.project_type,
            'projectTypeLabel': self.get_project_type_label(),
            'projectPrefix': self.project_prefix,
            'projectManager': self.project_manager,
            'status': self.status,
            'statusLabel': self.get_status_label(),
            'createdAt': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updatedAt': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def get_project_type_label(self):
        """获取项目类型标签"""
        labels = {
            'delivery': '项目交付',
            'research': '产研项目',
            'other': '其他项目'
        }
        return labels.get(self.project_type, '未知')

    def get_status_label(self):
        """获取项目状态标签"""
        labels = {
            'active': '进行中',
            'completed': '已完成',
            'suspended': '已暂停'
        }
        return labels.get(self.status, '未知')
