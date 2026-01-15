"""
系统配置表
"""
from datetime import datetime
from .db import db

class SysConfig(db.Model):
    """系统配置表"""
    __tablename__ = 'sys_config'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    config_value = db.Column(db.Text, nullable=False)
    config_type = db.Column(db.String(20), nullable=False, default='string')  # string/number/boolean/json
    category = db.Column(db.String(50), nullable=False, index=True)  # import/check/system
    description = db.Column(db.String(255))
    is_editable = db.Column(db.Integer, nullable=False, default=1)  # 1-可编辑/0-只读
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'configKey': self.config_key,
            'configValue': self.config_value,
            'configType': self.config_type,
            'category': self.category,
            'description': self.description,
            'isEditable': bool(self.is_editable)
        }
