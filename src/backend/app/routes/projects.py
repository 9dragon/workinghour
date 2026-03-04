"""
项目管理路由
"""
from flask import Blueprint, request
from app.models.db import db
from app.models.project import Project
from app.models.work_hour_data import WorkHourData
from app.utils.response import success_response, error_response
from app.utils.jwt_utils import auth_required
from sqlalchemy import func

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/projects', methods=['GET'])
@auth_required
def get_projects():
    """获取项目列表"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        project_code = request.args.get('projectCode', '')
        project_type = request.args.get('projectType', '')
        status = request.args.get('status', '')

        # 构建查询
        query = Project.query

        if project_code:
            query = query.filter(Project.project_code.like(f'%{project_code}%'))

        if project_type:
            query = query.filter(Project.project_type == project_type)

        if status:
            query = query.filter(Project.status == status)

        pagination = query.order_by(Project.created_at.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        projects = [p.to_dict() for p in pagination.items]

        return success_response(data={
            'list': projects,
            'total': pagination.total,
            'page': page,
            'size': size
        })

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@projects_bp.route('/projects/<int:project_id>', methods=['GET'])
@auth_required
def get_project_detail(project_id):
    """获取项目详情"""
    try:
        project = Project.query.get(project_id)
        if not project:
            return error_response(3001, '项目不存在', http_status=404)

        # 获取项目统计信息
        stats = db.session.query(
            func.sum(WorkHourData.work_hours).label('total_hours'),
            func.sum(WorkHourData.overtime_hours).label('total_overtime'),
            func.count(WorkHourData.id).label('record_count')
        ).filter(WorkHourData.project_id == project_id).first()

        data = project.to_dict()
        data['stats'] = {
            'totalHours': float(stats.total_hours or 0),
            'totalOvertime': float(stats.total_overtime or 0),
            'recordCount': stats.record_count or 0
        }

        return success_response(data=data)

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@projects_bp.route('/projects', methods=['POST'])
@auth_required
def create_project():
    """创建项目"""
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = ['projectCode', 'projectName', 'projectType']
        for field in required_fields:
            if field not in data or not data[field]:
                return error_response(1001, f'{field}不能为空', http_status=400)

        # 检查项目代码唯一性
        existing = Project.query.filter_by(project_code=data['projectCode']).first()
        if existing:
            return error_response(1002, '项目代码已存在', http_status=400)

        # 提取项目前缀
        project_code = data['projectCode']
        project_prefix = project_code[0].upper() if project_code else 'O'

        project = Project(
            project_code=data['projectCode'],
            project_name=data['projectName'],
            project_type=data['projectType'],
            project_prefix=project_prefix,
            project_manager=data.get('projectManager', ''),
            status=data.get('status', 'active')
        )

        db.session.add(project)
        db.session.commit()

        return success_response(data=project.to_dict(), message='创建成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@projects_bp.route('/projects/<int:project_id>', methods=['PUT'])
@auth_required
def update_project(project_id):
    """更新项目"""
    try:
        project = Project.query.get(project_id)
        if not project:
            return error_response(3001, '项目不存在', http_status=404)

        data = request.get_json()

        # 更新字段
        if 'projectName' in data:
            project.project_name = data['projectName']
        if 'projectManager' in data:
            project.project_manager = data['projectManager']
        if 'status' in data:
            project.status = data['status']

        db.session.commit()

        return success_response(data=project.to_dict(), message='更新成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@projects_bp.route('/projects/<int:project_id>', methods=['DELETE'])
@auth_required
def delete_project(project_id):
    """删除项目（软删除）"""
    try:
        project = Project.query.get(project_id)
        if not project:
            return error_response(3001, '项目不存在', http_status=404)

        # 检查是否有关联的工时记录
        record_count = WorkHourData.query.filter_by(project_id=project_id).count()
        if record_count > 0:
            return error_response(1003, f'该项目有{record_count}条工时记录，无法删除', http_status=400)

        db.session.delete(project)
        db.session.commit()

        return success_response(message='删除成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)
