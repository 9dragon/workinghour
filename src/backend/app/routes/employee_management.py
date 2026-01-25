"""
员工管理路由
"""
from flask import Blueprint, request
from app.models.db import db
from app.models.employee import Employee
from app.utils.response import success_response, error_response
from app.utils.jwt_utils import auth_required

employee_mgmt_bp = Blueprint('employee_management', __name__)


@employee_mgmt_bp.route('/employees', methods=['GET'])
@auth_required
def get_employees():
    """获取员工列表"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        keyword = request.args.get('keyword', '')

        query = Employee.query
        if keyword:
            query = query.filter(
                db.or_(
                    Employee.employee_name.like(f'%{keyword}%'),
                    Employee.dept_name.like(f'%{keyword}%')
                )
            )

        pagination = query.order_by(Employee.employee_name).paginate(
            page=page, per_page=size, error_out=False
        )

        employees = [emp.to_dict() for emp in pagination.items]

        return success_response(data={
            'list': employees,
            'total': pagination.total,
            'page': page,
            'size': size
        })

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@employee_mgmt_bp.route('/employees', methods=['POST'])
@auth_required
def create_employee():
    """创建员工"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('employeeName'):
            return error_response(7001, '员工姓名不能为空', http_status=400)
        if not data.get('deptName'):
            return error_response(7002, '部门不能为空', http_status=400)

        # 检查员工是否已存在
        existing = Employee.query.filter_by(employee_name=data['employeeName']).first()
        if existing:
            return error_response(7003, '该员工已存在', http_status=400)

        # 创建员工
        employee = Employee(
            employee_name=data['employeeName'],
            dept_name=data['deptName']
        )

        db.session.add(employee)
        db.session.commit()

        return success_response(data=employee.to_dict(), message='创建成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@employee_mgmt_bp.route('/employees/<int:employee_id>', methods=['PUT'])
@auth_required
def update_employee(employee_id):
    """更新员工信息"""
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return error_response(7004, '员工不存在', http_status=404)

        data = request.get_json()
        if 'deptName' in data:
            employee.dept_name = data['deptName']

        db.session.commit()
        return success_response(data=employee.to_dict(), message='更新成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@employee_mgmt_bp.route('/employees/<int:employee_id>', methods=['DELETE'])
@auth_required
def delete_employee(employee_id):
    """删除员工"""
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return error_response(7004, '员工不存在', http_status=404)

        db.session.delete(employee)
        db.session.commit()
        return success_response(message='删除成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)
