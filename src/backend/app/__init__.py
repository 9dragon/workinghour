"""
Flask应用工厂
"""
from flask import Flask
from flask_cors import CORS
from .models.db import db
from config import Config

def create_app(config_class=Config):
    """创建Flask应用实例"""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # 加载配置
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # 注册蓝图
    from .routes.auth import auth_bp
    from .routes.data import data_bp
    from .routes.import_data import import_bp
    from .routes.query import query_bp
    from .routes.check import check_bp
    from .routes.system import system_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(data_bp, url_prefix='/api/v1')
    app.register_blueprint(import_bp, url_prefix='/api/v1')
    app.register_blueprint(query_bp, url_prefix='/api/v1')
    app.register_blueprint(check_bp, url_prefix='/api/v1')
    app.register_blueprint(system_bp, url_prefix='/api/v1')

    # 创建数据库表
    with app.app_context():
        db.create_all()
        _init_default_data()

    return app

def _init_default_data():
    """初始化默认数据"""
    from .models.user import User
    from .models.sys_config import SysConfig

    # 创建默认管理员账户
    admin = User.query.filter_by(user_name='admin').first()
    if not admin:
        admin = User(
            user_name='admin',
            real_name='系统管理员',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)

    # 创建默认测试用户
    test_user = User.query.filter_by(user_name='test').first()
    if not test_user:
        test_user = User(
            user_name='test',
            real_name='测试用户',
            role='user'
        )
        test_user.set_password('test123')
        db.session.add(test_user)

    # 创建默认系统配置
    default_configs = [
        ('import.max_file_size', '10', 'number', 'import', '单次导入最大文件大小(MB)', 1),
        ('import.max_rows', '1000', 'number', 'import', '单次导入最大行数', 1),
        ('import.duplicate_strategy', 'skip', 'string', 'import', '重复数据处理策略(skip/cover)', 1),
        ('check.standard_hours', '8', 'number', 'check', '标准工作时长(小时)', 1),
        ('check.min_hours', '4', 'number', 'check', '最小工作时长(小时)', 1),
        ('check.max_overtime', '4', 'number', 'check', '单日最大加班时长(小时)', 1),
        ('check.max_monthly_overtime', '80', 'number', 'check', '月度最大加班时长(小时)', 1),
        ('check.workdays', '[1,2,3,4,5]', 'json', 'check', '标准工作日(1-7,周一到周日)', 1),
    ]

    for key, value, type_, category, desc, editable in default_configs:
        config = SysConfig.query.filter_by(config_key=key).first()
        if not config:
            config = SysConfig(
                config_key=key,
                config_value=value,
                config_type=type_,
                category=category,
                description=desc,
                is_editable=editable
            )
            db.session.add(config)

    db.session.commit()
