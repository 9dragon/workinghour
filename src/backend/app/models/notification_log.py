"""
通知发送日志表

记录每次通知发送的结果，便于事后审计"哪些员工被发了什么、成功没"。
"""
from datetime import datetime
from .db import db


class NotificationLog(db.Model):
    """单次通知发送记录"""
    __tablename__ = 'notification_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    check_no = db.Column(db.String(50), index=True)
    employee_name = db.Column(db.String(50), index=True)
    dept_name = db.Column(db.String(50))
    channel = db.Column(db.String(20), index=True)        # dingtalk / email
    status = db.Column(db.String(20), index=True)         # success / failed / skipped
    error_message = db.Column(db.Text)
    content = db.Column(db.Text)                          # 实际发出的消息体（钉钉=markdown 文本，邮件=HTML 源码）
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'checkNo': self.check_no,
            'employeeName': self.employee_name,
            'deptName': self.dept_name,
            'channel': self.channel,
            'status': self.status,
            'errorMessage': self.error_message,
            'content': self.content,
            'sentAt': self.sent_at.isoformat() if self.sent_at else None
        }
