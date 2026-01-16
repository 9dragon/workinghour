"""
工时数据主表
"""
from datetime import datetime, date
from .db import db

class WorkHourData(db.Model):
    """工时数据主表"""
    __tablename__ = 'work_hour_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # 钉钉原始数据字段（对应需求15个核心字段）
    serial_no = db.Column(db.String(50), nullable=False, default='')
    user_name = db.Column(db.String(50), nullable=False, index=True)
    start_time = db.Column(db.Date, nullable=False, index=True)
    end_time = db.Column(db.Date, nullable=False)
    project_manager = db.Column(db.String(50))
    project_name = db.Column(db.String(100), nullable=False, index=True)
    work_hours = db.Column(db.Float, nullable=False)
    overtime_hours = db.Column(db.Float, nullable=False, default=0)
    work_content = db.Column(db.String(500))
    create_time = db.Column(db.DateTime)  # OA创建时间
    current_leader = db.Column(db.String(50))
    approval_result = db.Column(db.String(10), nullable=False, default='通过')
    approval_status = db.Column(db.String(10), nullable=False, default='已完成')
    update_time = db.Column(db.DateTime)  # OA更新时间
    dept_name = db.Column(db.String(50), nullable=False, index=True)

    # 系统扩展字段
    import_batch_no = db.Column(db.String(50), nullable=False, index=True)
    import_time = db.Column(db.DateTime, nullable=False, default=datetime.now)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        """转换为字典"""
        # 格式化时间为 yyyy-MM-dd HH:mm:ss
        import_time_str = None
        if self.import_time:
            import_time_str = self.import_time.strftime('%Y-%m-%d %H:%M:%S')

        # 格式化日期为 yyyy-MM-dd
        start_time_str = None
        if self.start_time:
            start_time_str = self.start_time.strftime('%Y-%m-%d') if isinstance(self.start_time, date) else str(self.start_time)

        end_time_str = None
        if self.end_time:
            end_time_str = self.end_time.strftime('%Y-%m-%d') if isinstance(self.end_time, date) else str(self.end_time)

        return {
            'id': self.id,
            'serialNo': self.serial_no,
            'userName': self.user_name,
            'startTime': start_time_str,
            'endTime': end_time_str,
            'projectManager': self.project_manager,
            'projectName': self.project_name,
            'workHours': self.work_hours,
            'overtimeHours': self.overtime_hours,
            'deptName': self.dept_name,
            'workContent': self.work_content,
            'approvalResult': self.approval_result,
            'approvalStatus': self.approval_status,
            'importTime': import_time_str
        }
