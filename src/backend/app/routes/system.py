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
    """备份数据库"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'app.db')
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')

        # 创建备份目录
        os.makedirs(backup_dir, exist_ok=True)

        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)

        # 复制数据库文件
        shutil.copy2(db_path, backup_path)

        # 获取文件大小
        file_size = os.path.getsize(backup_path)

        return success_response(data={
            'filename': backup_filename,
            'filePath': backup_path,
            'fileSize': file_size,
            'backupTime': datetime.now().isoformat()
        }, message='备份成功')

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@system_bp.route('/system/restore', methods=['POST'])
@auth_required
def restore_database():
    """恢复数据库"""
    try:
        data = request.get_json()
        backup_filename = data.get('filename')

        if not backup_filename:
            return error_response(6001, '未指定备份文件'), 400

        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        backup_path = os.path.join(backup_dir, backup_filename)

        if not os.path.exists(backup_path):
            return error_response(6002, '备份文件不存在'), 404

        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'app.db')

        # 先备份当前数据库
        current_backup = os.path.join(backup_dir, f'before_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(db_path, current_backup)

        # 恢复数据库
        shutil.copy2(backup_path, db_path)

        return success_response(data={
            'restoredFrom': backup_filename,
            'previousBackup': os.path.basename(current_backup),
            'restoreTime': datetime.now().isoformat()
        }, message='恢复成功')

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@system_bp.route('/system/backups', methods=['GET'])
def list_backups():
    """获取备份文件列表"""
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')

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
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'app.db')

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
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
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
