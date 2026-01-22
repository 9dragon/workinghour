"""
系统设置路由
"""
from flask import Blueprint, request, send_file
from app.models.db import db
from app.models.sys_config import SysConfig
from app.utils.response import success_response, error_response
from app.utils.jwt_utils import auth_required
import os
import sqlite3
from datetime import datetime
import shutil

system_bp = Blueprint('system', __name__)


@system_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点（无需认证）"""
    return success_response(data={'status': 'healthy', 'service': 'workinghour-backend'})


@system_bp.route('/system/config', methods=['GET'])
def get_system_config():
    """获取系统配置"""
    try:
        category = request.args.get('category', '')

        query = SysConfig.query

        if category:
            query = query.filter_by(category=category)

        configs = query.order_by(SysConfig.category, SysConfig.id).all()

        # 按分类组织
        result = {}
        for config in configs:
            cat = config.category
            if cat not in result:
                result[cat] = []
            result[cat].append(config.to_dict())

        return success_response(data=result)

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@system_bp.route('/system/config', methods=['PUT'])
@auth_required
def update_system_config():
    """更新系统配置"""
    try:
        data = request.get_json()
        configs = data.get('configs', [])

        for item in configs:
            config = SysConfig.query.filter_by(config_key=item.get('configKey')).first()

            if not config:
                return error_response(5001, f"配置项{item.get('configKey')}不存在"), 404

            if not config.is_editable:
                return error_response(5002, f"配置项{config.config_key}为只读，不能修改"), 400

            # 类型验证
            if config.config_type == 'number':
                try:
                    float(item.get('configValue'))
                except:
                    return error_response(5003, f"{config.config_key}的值必须为数字"), 400

            elif config.config_type == 'boolean':
                if item.get('configValue') not in ['true', 'false', '0', '1']:
                    return error_response(5003, f"{config.config_key}的值必须为布尔值"), 400

            config.config_value = str(item.get('configValue'))

        db.session.commit()

        return success_response(message='配置更新成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e)), 500


@system_bp.route('/system/backup', methods=['POST'])
@auth_required
def backup_database():
    """备份数据库并返回文件下载"""
    try:
        from config import Config

        # 使用配置文件中的数据库路径
        db_path = Config.DATABASE_PATH
        backup_dir = os.path.join(Config.BASE_DIR, 'backups')

        # 创建备份目录
        os.makedirs(backup_dir, exist_ok=True)

        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            return error_response(6004, f'数据库文件不存在: {db_path}'), 404

        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)

        # 复制数据库文件
        shutil.copy2(db_path, backup_path)

        # 返回文件供下载
        return send_file(
            backup_path,
            mimetype='application/x-sqlite3',
            as_attachment=True,
            download_name=backup_filename
        )

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@system_bp.route('/system/restore', methods=['POST'])
@auth_required
def restore_database():
    """从上传的文件恢复数据库"""
    try:
        from config import Config

        # 检查是否有上传的文件
        if 'file' not in request.files:
            return error_response(6001, '未上传备份文件'), 400

        file = request.files['file']
        if file.filename == '':
            return error_response(6001, '未上传备份文件'), 400

        # 验证文件扩展名
        if not file.filename.endswith('.db'):
            return error_response(6003, '备份文件格式错误，仅支持.db文件'), 400

        # 保存上传的文件到临时位置
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            file.save(tmp_file.name)
            tmp_path = tmp_file.name

        # 使用配置文件中的数据库路径
        db_path = Config.DATABASE_PATH
        backup_dir = os.path.join(Config.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # 检查当前数据库是否存在
        if not os.path.exists(db_path):
            return error_response(6005, '当前数据库文件不存在，无法恢复'), 404

        # 先备份当前数据库
        current_backup = os.path.join(backup_dir, f'before_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(db_path, current_backup)

        # 恢复数据库
        shutil.copy2(tmp_path, db_path)

        # 删除临时文件
        os.unlink(tmp_path)

        return success_response(data={
            'restoredFrom': file.filename,
            'previousBackup': os.path.basename(current_backup),
            'restoreTime': datetime.now().isoformat()
        }, message='恢复成功')

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@system_bp.route('/system/backups', methods=['GET'])
def list_backups():
    """获取备份文件列表"""
    try:
        from config import Config
        backup_dir = os.path.join(Config.BASE_DIR, 'backups')

        if not os.path.exists(backup_dir):
            return success_response(data=[])

        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith('.db'):
                file_path = os.path.join(backup_dir, filename)
                stat = os.stat(file_path)
                backups.append({
                    'filename': filename,
                    'fileSize': stat.st_size,
                    'createTime': datetime.fromtimestamp(stat.st_ctime).isoformat()
                })

        # 按创建时间倒序排列
        backups.sort(key=lambda x: x['createTime'], reverse=True)

        return success_response(data=backups)

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@system_bp.route('/system/info', methods=['GET'])
def get_system_info():
    """获取系统信息"""
    try:
        from config import Config
        db_path = Config.DATABASE_PATH

        # 获取数据库大小
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

        # 获取数据统计
        from app.models.work_hour_data import WorkHourData
        from app.models.import_record import ImportRecord
        from app.models.user import User

        total_records = WorkHourData.query.count()
        total_imports = ImportRecord.query.count()
        total_users = User.query.count()

        # 获取最新导入时间
        latest_import = ImportRecord.query.order_by(
            ImportRecord.import_time.desc()
        ).first()

        # 获取备份文件数量
        backup_dir = os.path.join(Config.BASE_DIR, 'backups')
        backup_count = len([f for f in os.listdir(backup_dir)]) if os.path.exists(backup_dir) else 0

        return success_response(data={
            'dbSize': db_size,
            'totalRecords': total_records,
            'totalImports': total_imports,
            'totalUsers': total_users,
            'latestImportTime': latest_import.import_time.isoformat() if latest_import else None,
            'backupCount': backup_count,
            'systemVersion': '1.0.0'
        })

    except Exception as e:
        return error_response(500, str(e), http_status=500)
