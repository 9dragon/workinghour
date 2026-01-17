"""
数据字典路由
"""
from flask import Blueprint
from app.models.db import db
from app.models.work_hour_data import WorkHourData
from app.utils.response import success_response, error_response

data_bp = Blueprint('data', __name__)


@data_bp.route('/data/dict', methods=['GET'])
def get_data_dict():
    """获取数据字典"""
    try:
        # 获取所有项目名称
        projects = db.session.query(
            WorkHourData.project_name
        ).distinct().filter(
            WorkHourData.project_name.isnot(None)
        ).all()

        # 获取所有项目经理名称
        managers = db.session.query(
            WorkHourData.project_manager
        ).distinct().filter(
            WorkHourData.project_manager.isnot(None),
            WorkHourData.project_manager != ''
        ).all()

        # 获取项目与经理的关联关系
        project_manager = db.session.query(
            WorkHourData.project_name,
            WorkHourData.project_manager
        ).distinct().filter(
            WorkHourData.project_name.isnot(None),
            WorkHourData.project_manager.isnot(None),
            WorkHourData.project_manager != ''
        ).all()

        # 构建项目和经理的映射关系
        project_manager_map = {}
        manager_project_map = {}

        for project, manager in project_manager:
            if project and manager:
                if project not in project_manager_map:
                    project_manager_map[project] = []
                if manager not in project_manager_map[project]:
                    project_manager_map[project].append(manager)

                if manager not in manager_project_map:
                    manager_project_map[manager] = []
                if project not in manager_project_map[manager]:
                    manager_project_map[manager].append(project)

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
            'projects': [p[0] for p in projects if p[0]],
            'managers': [m[0] for m in managers if m[0]],
            'projectManagerMap': project_manager_map,  # 项目 -> 经理列表
            'managerProjectMap': manager_project_map,  # 经理 -> 项目列表
            'departments': [d[0] for d in departments if d[0]],
            'users': [u[0] for u in users if u[0]]  # 用户名列表
        })

    except Exception as e:
        return error_response(500, str(e), http_status=500)
