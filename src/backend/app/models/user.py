"""
系统用户表
"""
from datetime import datetime
from .db import db
import bcrypt

class User(db.Model):
    """系统用户表"""
    __tablename__ = 'sys_users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)  # bcrypt加密后的密码
    role = db.Column(db.String(20), nullable=False, default='user')  # admin/user
    email = db.Column(db.String(100))
    status = db.Column(db.String(20), nullable=False, default='active', index=True)  # active/locked
    login_fail_count = db.Column(db.Integer, nullable=False, default=0)
    lock_time = db.Column(db.DateTime)
    last_login_time = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def set_password(self, password):
        """设置密码（bcrypt加密）"""
        salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password):
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def check_password(self, password):
        """验证密码（别名）"""
        return self.verify_password(password)

    def is_locked(self):
        """检查账号是否被锁定"""
        if self.lock_time is None:
            return False
        # 锁定30分钟后自动解锁
        lock_duration = (datetime.now() - self.lock_time).total_seconds() / 60
        return lock_duration < 30

    def get_lock_remaining_time(self):
        """获取锁定剩余时间（分钟）"""
        if self.lock_time is None:
            return 0
        elapsed_minutes = (datetime.now() - self.lock_time).total_seconds() / 60
        remaining = 30 - elapsed_minutes
        return max(0, int(remaining))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'userName': self.user_name,
            'role': self.role,
            'email': self.email,
            'status': self.status,
            'lastLoginTime': self.last_login_time.isoformat() if self.last_login_time else None
        }
