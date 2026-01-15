"""
项目工时统计系统 - 配置文件
"""
import os
from datetime import timedelta

class Config:
    """基础配置"""
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # 数据库配置
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or os.path.join(BASE_DIR, 'instance', 'workinghour.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_ALGORITHM = 'HS256'

    # 文件上传配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'instance/uploads'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'xls', 'xlsx'}
    MAX_IMPORT_ROWS = 1000

    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    # 导入批次号格式
    BATCH_NO_PREFIX = 'IMP'
    CHECK_NO_PREFIX = 'CHK'

    # CORS配置
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')

    # 工时核对规则配置
    INTEGRITY_DEFAULT_WORKDAYS = [1, 2, 3, 4, 5]  # 周一到周五
    COMPLIANCE_STANDARD_HOURS = 8
    COMPLIANCE_MIN_HOURS = 4
    COMPLIANCE_MAX_OVERTIME = 4
    COMPLIANCE_MAX_MONTHLY_OVERTIME = 80

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
