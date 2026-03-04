"""
数据字典路由
"""
from flask import Blueprint
from app.models.db import db
from app.models.work_hour_data import WorkHourData
from app.models.project import Project
from app.utils.response import success_response, error_response

data_bp = Blueprint('data', __name__)


@data_bp.route('/data/dict', methods=['GET'])
def get_data_dict():
    """获取数据字典"""
    try:
        # 从 projects 表获取所有活跃的项目
        projects_query = Project.query.filter_by(status='active').all()
        projects = [p.project_name for p in projects_query]

        # 获取所有项目经理（从 projects 表）
        managers_query = db.session.query(
            Project.project_manager
        ).distinct().filter(
            Project.project_manager.isnot(None),
            Project.project_manager != '',
            Project.status == 'active'
        ).all()
        managers = [m[0] for m in managers_query]

        # 构建项目和经理的映射关系（从 projects 表）
        project_manager_map = {}
        manager_project_map = {}

        for p in projects_query:
            if p.project_name and p.project_manager:
                if p.project_name not in project_manager_map:
                    project_manager_map[p.project_name] = []
                if p.project_manager not in project_manager_map[p.project_name]:
                    project_manager_map[p.project_name].append(p.project_manager)

                if p.project_manager not in manager_project_map:
                    manager_project_map[p.project_manager] = []
                if p.project_name not in manager_project_map[p.project_manager]:
                    manager_project_map[p.project_manager].append(p.project_name)

        # 获取所有部门名称
        departments = db.session.query(
            WorkHourData.dept_name
        ).distinct().filter(
            WorkHourData.dept_name.isnot(None)
        ).all()

        # 获取所有用户名（只查询用户名字段进行去重）
        users = db.session.query(
            WorkHourData.user_name
        ).distinct().filter(
            WorkHourData.user_name.isnot(None)
        ).all()

        return success_response(data={
            'projects': [p for p in projects if p],
            'managers': managers,
            'projectManagerMap': project_manager_map,  # 项目 -> 经理列表
            'managerProjectMap': manager_project_map,  # 经理 -> 项目列表
            'departments': [d[0] for d in departments if d[0]],
            'users': [u[0] for u in users if u[0]]  # 用户名列表
        })

    except Exception as e:
        return error_response(500, str(e), http_status=500)
