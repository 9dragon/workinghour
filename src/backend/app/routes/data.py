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

        # 获取所有部门名称
        departments = db.session.query(
            WorkHourData.dept_name
        ).distinct().filter(
            WorkHourData.dept_name.isnot(None)
        ).all()

        # 获取所有用户名
        users = db.session.query(
            WorkHourData.user_name,
            WorkHourData.dept_name
        ).distinct().filter(
            WorkHourData.user_name.isnot(None)
        ).all()

        return success_response(data={
            'projects': [p[0] for p in projects if p[0]],
            'departments': [d[0] for d in departments if d[0]],
            'users': [
                {
                    'userName': u[0],
                    'deptName': u[1] or ''
                }
                for u in users if u[0]
            ]
        })

    except Exception as e:
        return error_response(500, str(e), http_status=500)
