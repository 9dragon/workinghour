"""
节假日管理表
"""
from datetime import datetime
from .db import db

class Holiday(db.Model):
    """节假日表"""
    __tablename__ = 'holidays'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    holiday_date = db.Column(db.Date, nullable=False, unique=True, index=True)
    holiday_name = db.Column(db.String(50), nullable=False)
    is_workday = db.Column(db.Boolean, nullable=False, default=False)  # 调休工作日
    is_weekend = db.Column(db.Boolean, nullable=False, default=False)  # 是否为周末
    data_source = db.Column(db.String(20), nullable=False, default='manual')  # manual/api/auto
    year = db.Column(db.Integer, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    created_by = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'holidayDate': self.holiday_date.isoformat(),
            'holidayName': self.holiday_name,
            'isWorkday': self.is_workday,
            'isWeekend': self.is_weekend,
            'dataSource': self.data_source,
            'year': self.year,
            'createdAt': self.created_at.isoformat(),
            'createdBy': self.created_by
        }
