"""
核对记录表
"""
from datetime import datetime
from .db import db

class CheckRecord(db.Model):
    """核对批次记录表"""
    __tablename__ = 'check_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    check_no = db.Column(db.String(50), unique=True, nullable=False, index=True)
    check_type = db.Column(db.String(20), nullable=False, index=True)  # integrity/compliance
    start_date = db.Column(db.Date, nullable=True)  # 允许为NULL以支持全量查询
    end_date = db.Column(db.Date, nullable=True)  # 允许为NULL以支持全量查询
    dept_name = db.Column(db.String(50), index=True)
    user_name = db.Column(db.String(50), index=True)
    check_config = db.Column(db.Text, nullable=False)  # JSON格式配置
    check_result = db.Column(db.Text, nullable=False)  # JSON格式结果
    check_details = db.Column(db.Text, nullable=True)  # JSON格式详细列表（可选）
    trigger_type = db.Column(db.String(20), nullable=False, default='manual')  # manual/scheduled/import
    check_user = db.Column(db.String(50), nullable=False)
    check_time = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    report_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'checkNo': self.check_no,
            'checkType': self.check_type,
            'triggerType': self.trigger_type,
            'startDate': self.start_date.isoformat() if self.start_date else None,
            'endDate': self.end_date.isoformat() if self.end_date else None,
            'deptName': self.dept_name,
            'userName': self.user_name,
            'checkUser': self.check_user,
            'checkTime': self.check_time.isoformat() if self.check_time else None
        }
