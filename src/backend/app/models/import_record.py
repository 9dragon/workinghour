"""
导入记录表
"""
from datetime import datetime
from .db import db

class ImportRecord(db.Model):
    """导入批次记录表"""
    __tablename__ = 'import_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    batch_no = db.Column(db.String(50), unique=True, nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False, default=0)
    total_rows = db.Column(db.Integer, nullable=False, default=0)
    success_rows = db.Column(db.Integer, nullable=False, default=0)
    repeat_rows = db.Column(db.Integer, nullable=False, default=0)
    invalid_rows = db.Column(db.Integer, nullable=False, default=0)
    duplicate_strategy = db.Column(db.String(20), nullable=False, default='skip')
    import_user = db.Column(db.String(50), nullable=False, index=True)
    import_time = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    report_path = db.Column(db.String(255))
    error_details = db.Column(db.Text)  # JSON格式存储错误详情
    repeat_details = db.Column(db.Text)  # JSON格式存储重复数据详情
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        """转换为字典"""
        # 格式化时间为 yyyy-MM-dd HH:mm:ss
        import_time_str = None
        if self.import_time:
            import_time_str = self.import_time.strftime('%Y-%m-%d %H:%M:%S')

        return {
            'id': self.id,
            'batchNo': self.batch_no,
            'fileName': self.file_name,
            'totalRows': self.total_rows,
            'successRows': self.success_rows,
            'repeatRows': self.repeat_rows,
            'invalidRows': self.invalid_rows,
            'importUser': self.import_user,
            'importTime': import_time_str,
            'fileSize': self.file_size,
            'duplicateStrategy': self.duplicate_strategy,
            'errorDetails': self.error_details,
            'repeatDetails': self.repeat_details
        }
