"""
预算管理路由
"""
from flask import Blueprint, request
from app.models.db import db
from app.models.employee import Employee
from app.models.project_budget import ProjectBudget
from app.models.work_hour_data import WorkHourData
from app.utils.response import success_response, error_response, paginated_response
from app.utils.jwt_utils import auth_required
from sqlalchemy import func, and_
from decimal import Decimal

budget_bp = Blueprint('budget', __name__)


# ==================== 员工角色管理 ====================

@budget_bp.route('/budget/employee-roles', methods=['GET'])
@auth_required
def get_employee_role():
    """获取员工角色列表（分页、筛选）"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        keyword = request.args.get('keyword', '')
        role_filter = request.args.get('role', '')
        dept_filter = request.args.get('dept', '')

        query = Employee.query

        # 关键词搜索（改为仅搜索姓名）
        if keyword:
            query = query.filter(Employee.employee_name.like(f'%{keyword}%'))

        # 部门筛选（新增）
        if dept_filter:
            query = query.filter(Employee.dept_name == dept_filter)

        # 角色筛选
        if role_filter:
            query = query.filter(Employee.role == role_filter)

        # 按姓名排序
        query = query.order_by(Employee.employee_name)

        # 分页
        pagination = query.paginate(page=page, per_page=size, error_out=False)

        employees = [emp.to_dict() for emp in pagination.items]

        return success_response(data={
            'list': employees,
            'total': pagination.total,
            'page': page,
            'size': size
        })

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@budget_bp.route('/budget/employee-roles/<int:employee_id>', methods=['PUT'])
@auth_required
def update_employee_role(employee_id):
    """更新员工角色"""
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return error_response(8001, '员工不存在', http_status=404)

        data = request.get_json()
        new_role = data.get('role')

        # 验证角色值
        valid_roles = ['project_manager', 'data_collection', 'software_dev', 'staff']
        if new_role not in valid_roles:
            return error_response(8002, '无效的角色值', http_status=400)

        employee.role = new_role
        db.session.commit()

        return success_response(data=employee.to_dict(), message='角色更新成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@budget_bp.route('/budget/employee-roles/batch', methods=['PUT'])
@auth_required
def batch_update_employee_roles():
    """批量更新员工角色"""
    try:
        data = request.get_json()
        employee_ids = data.get('employeeIds', [])
        new_role = data.get('role')

        if not employee_ids:
            return error_response(8003, '员工ID列表不能为空', http_status=400)

        # 验证角色值
        valid_roles = ['project_manager', 'data_collection', 'software_dev', 'staff']
        if new_role not in valid_roles:
            return error_response(8002, '无效的角色值', http_status=400)

        # 批量更新
        employees = Employee.query.filter(Employee.id.in_(employee_ids)).all()

        if not employees:
            return error_response(8001, '未找到任何员工', http_status=404)

        updated_count = 0
        for employee in employees:
            employee.role = new_role
            updated_count += 1

        db.session.commit()

        return success_response(
            data={'updatedCount': updated_count},
            message=f'成功更新 {updated_count} 位员工的角色'
        )

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@budget_bp.route('/budget/employees-by-role', methods=['GET'])
@auth_required
def get_employees_by_role():
    """按角色获取员工列表（下拉选择用）"""
    try:
        role = request.args.get('budgetType', '')
        project_code = request.args.get('projectCode', '')

        query = Employee.query

        if role:
            query = query.filter(Employee.role == role)

        employees = query.order_by(Employee.employee_name).all()

        # 返回简化的员工列表
        employee_list = [
            {
                'id': emp.id,
                'employeeName': emp.employee_name,
                'deptName': emp.dept_name
            }
            for emp in employees
        ]

        return success_response(data=employee_list)

    except Exception as e:
        return error_response(500, str(e), http_status=500)


# ==================== 预算管理 ====================

@budget_bp.route('/budget/projects', methods=['POST'])
@auth_required
def create_budget():
    """创建项目预算"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('projectCode'):
            return error_response(8101, '项目代码不能为空', http_status=400)
        if not isinstance(data.get('budgetHours'), (int, float)) or data.get('budgetHours') < 0:
            return error_response(8103, '预算工时必须是非负数', http_status=400)
        if data.get('budgetType') not in ['project_manager', 'data_collection', 'software_dev']:
            return error_response(8104, '无效的类型值', http_status=400)

        # 检查项目是否存在
        from app.models.project import Project
        project = Project.query.filter_by(project_code=data['projectCode']).first()
        if not project:
            return error_response(8106, '项目不存在', http_status=400)

        # 检查是否已存在相同的预算记录
        existing = ProjectBudget.query.filter_by(
            project_code=data['projectCode'],
            budget_type=data['budgetType']
        ).first()

        if existing:
            return error_response(8105, '该项目已存在该类型的预算', http_status=400)

        # 创建预算记录
        budget = ProjectBudget(
            project_name=project.project_name,  # 从项目表获取名称
            project_code=data['projectCode'],
            budget_type=data['budgetType'],
            budget_hours=Decimal(str(data['budgetHours']))
        )

        db.session.add(budget)
        db.session.commit()

        return success_response(data=budget.to_dict(), message='预算创建成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@budget_bp.route('/budget/projects/<int:budget_id>', methods=['PUT'])
@auth_required
def update_budget(budget_id):
    """更新预算"""
    try:
        budget = ProjectBudget.query.get(budget_id)
        if not budget:
            return error_response(8106, '预算记录不存在', http_status=404)

        data = request.get_json()

        # 更新字段
        if 'budgetHours' in data:
            if not isinstance(data['budgetHours'], (int, float)) or data['budgetHours'] < 0:
                return error_response(8103, '预算工时必须是非负数', http_status=400)
            budget.budget_hours = Decimal(str(data['budgetHours']))

        db.session.commit()

        return success_response(data=budget.to_dict(), message='预算更新成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@budget_bp.route('/budget/projects/<int:budget_id>', methods=['DELETE'])
@auth_required
def delete_budget(budget_id):
    """删除预算"""
    try:
        budget = ProjectBudget.query.get(budget_id)
        if not budget:
            return error_response(8106, '预算记录不存在', http_status=404)

        db.session.delete(budget)
        db.session.commit()

        return success_response(message='预算删除成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@budget_bp.route('/budget/projects', methods=['GET'])
@auth_required
def get_budgets():
    """获取预算列表"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        project_code = request.args.get('projectCode', '')
        budget_type = request.args.get('budgetType', '')

        # 构建查询
        query = ProjectBudget.query

        if project_code:
            query = query.filter(ProjectBudget.project_code.like(f'%{project_code}%'))

        if budget_type:
            query = query.filter(ProjectBudget.budget_type == budget_type)

        # 按项目代码排序
        query = query.order_by(ProjectBudget.project_code)

        # 分页
        pagination = query.paginate(page=page, per_page=size, error_out=False)

        budgets = [budget.to_dict() for budget in pagination.items]

        return success_response(data={
            'list': budgets,
            'total': pagination.total,
            'page': page,
            'size': size
        })

    except Exception as e:
        return error_response(500, str(e), http_status=500)



# ==================== 预算统计 ====================

@budget_bp.route('/budget/statistics/summary', methods=['GET'])
@auth_required
def get_statistics_summary():
    """预算统计汇总"""
    try:
        project_code = request.args.get('projectCode', '')

        # 构建预算查询
        budget_query = ProjectBudget.query

        if project_code:
            budget_query = budget_query.filter(ProjectBudget.project_code == project_code)

        # 计算总预算工时
        budget_result = budget_query.with_entities(
            func.sum(ProjectBudget.budget_hours)
        ).first()

        total_budget_hours = float(budget_result[0]) if budget_result and budget_result[0] else 0

        # 构建实际工时查询
        work_hours_query = db.session.query(
            func.sum(WorkHourData.work_hours)
        )

        # 直接按 work_type 统计（不再关联员工表）
        work_type_list = ['project_delivery', 'product_research', 'presales_support']
        work_hours_query = work_hours_query.filter(
            WorkHourData.work_type.in_(work_type_list)
        )

        # 按项目筛选
        if project_code:
            # 通过 project_code 找到项目，使用 project_id 进行关联
            from app.models.project import Project
            project = Project.query.filter_by(project_code=project_code).first()
            if project:
                work_hours_query = work_hours_query.filter(
                    WorkHourData.project_id == project.id
                )

        actual_result = work_hours_query.first()
        total_actual_hours = float(actual_result[0]) if actual_result and actual_result[0] else 0
        # 转换为"人天"（1人天 = 8小时）
        total_actual_hours = total_actual_hours / 8

        # 计算完成率
        completion_rate = (total_actual_hours / total_budget_hours * 100) if total_budget_hours > 0 else 0

        return success_response(data={
            'totalBudgetHours': round(total_budget_hours, 2),
            'totalActualHours': round(total_actual_hours, 2),
            'completionRate': round(completion_rate, 2)
        })

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@budget_bp.route('/budget/statistics/by-project', methods=['GET'])
@auth_required
def get_statistics_by_project():
    """按项目统计预算执行情况"""
    try:
        project_code = request.args.get('projectCode', '')

        # 构建查询
        query = db.session.query(
            ProjectBudget.project_name,
            ProjectBudget.project_code,
            ProjectBudget.budget_type,
            ProjectBudget.budget_hours
        )

        if project_code:
            query = query.filter(ProjectBudget.project_code == project_code)

        budgets = query.all()

        result = []

        # 预先查询所有项目信息
        from app.models.project import Project
        project_codes = [b.project_code for b in budgets]
        projects = Project.query.filter(Project.project_code.in_(project_codes)).all()
        project_map = {p.project_code: p for p in projects}

        for budget in budgets:
            # 根据预算类型确定对应的员工角色
            budget_type_to_role = {
                'project_manager': 'project_manager',
                'data_collection': 'data_collection',
                'software_dev': 'software_dev'
            }
            target_role = budget_type_to_role.get(budget.budget_type)

            # 查询该角色的所有员工姓名
            employee_names = []
            if target_role:
                role_employees = Employee.query.filter_by(role=target_role).all()
                employee_names = [emp.employee_name for emp in role_employees]

            # 查询实际工时：根据员工角色统计项目交付工时
            actual_hours_query = db.session.query(
                func.sum(WorkHourData.work_hours)
            ).filter(
                WorkHourData.work_type == 'project_delivery'
            )

            # 按员工角色筛选
            if employee_names:
                actual_hours_query = actual_hours_query.filter(
                    WorkHourData.user_name.in_(employee_names)
                )

            # 通过 project_code 找到对应的 project，使用 project_id 筛选
            if budget.project_code in project_map:
                project = project_map[budget.project_code]
                actual_hours_query = actual_hours_query.filter(
                    WorkHourData.project_id == project.id
                )
            else:
                # 如果找不到项目，通过 project_name 匹配（兜底逻辑）
                actual_hours_query = actual_hours_query.filter(
                    WorkHourData.project_name == budget.project_name
                )

            actual_result = actual_hours_query.first()
            actual_hours = float(actual_result[0]) if actual_result and actual_result[0] else 0
            # 转换为"人天"（1人天 = 8小时）
            actual_hours = actual_hours / 8

            # 计算完成率
            budget_hours = float(budget.budget_hours)
            completion_rate = (actual_hours / budget_hours * 100) if budget_hours > 0 else 0

            result.append({
                'projectName': budget.project_name,
                'projectCode': budget.project_code,
                'budgetType': budget.budget_type,
                'budgetTypeLabel': ProjectBudget(budget_type=budget.budget_type).get_budget_type_label(),
                'budgetHours': budget_hours,
                'actualHours': round(actual_hours, 2),
                'completionRate': round(completion_rate, 2)
            })

        return success_response(data=result)

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@budget_bp.route('/budget/statistics/by-employee', methods=['GET'])
@auth_required
def get_statistics_by_employee():
    """按员工统计（含详情）"""
    try:
        project_code = request.args.get('projectCode', '')
        role = request.args.get('budgetType', '')

        # 构建员工查询：统计所有有项目交付工时记录的员工
        subquery = db.session.query(
            WorkHourData.user_name
        ).filter(
            WorkHourData.work_type == 'project_delivery'
        ).distinct().subquery()

        employee_query = Employee.query.filter(
            Employee.employee_name.in_(subquery)
        )

        # 如果指定了角色筛选，直接按员工角色筛选
        if role:
            # 将 budget_type 映射到 employee_role
            role_map = {
                'project_manager': 'project_manager',
                'data_collection': 'data_collection',
                'software_dev': 'software_dev'
            }
            target_role = role_map.get(role)
            if target_role:
                employee_query = employee_query.filter(Employee.role == target_role)

        employees = employee_query.all()

        result = []

        # 获取项目信息（用于筛选）
        project = None
        if project_code:
            from app.models.project import Project
            project = Project.query.filter_by(project_code=project_code).first()

        for employee in employees:
            # 查询该员工的实际工时（项目交付类型）
            work_hours_query = db.session.query(
                func.sum(WorkHourData.work_hours)
            ).filter(
                WorkHourData.user_name == employee.employee_name,
                WorkHourData.work_type == 'project_delivery'
            )

            # 按项目筛选
            if project:
                work_hours_query = work_hours_query.filter(
                    WorkHourData.project_id == project.id
                )

            work_hours_result = work_hours_query.first()
            total_hours = float(work_hours_result[0]) if work_hours_result and work_hours_result[0] else 0
            # 转换为"人天"（1人天 = 8小时）
            total_hours = total_hours / 8

            # 查询该员工在各项目的工时分布（应用项目筛选）
            project_distribution = db.session.query(
                WorkHourData.project_name,
                func.sum(WorkHourData.work_hours).label('hours')
            ).filter(
                WorkHourData.user_name == employee.employee_name,
                WorkHourData.work_type == 'project_delivery'
            )

            # 应用项目筛选
            if project:
                project_distribution = project_distribution.filter(
                    WorkHourData.project_id == project.id
                )

            project_distribution = project_distribution.group_by(
                WorkHourData.project_name
            ).all()

            projects = [
                {
                    'projectName': item[0],
                    'hours': round(float(item[1]) / 8, 2)  # 转换为"人天"
                }
                for item in project_distribution
            ]

            # 只添加工时大于0的员工
            if total_hours > 0:
                result.append({
                    'id': employee.id,
                    'employeeName': employee.employee_name,
                    'deptName': employee.dept_name,
                    'role': employee.role,
                    'roleLabel': employee.get_role_label(),
                    'totalHours': round(total_hours, 2),
                    'projects': projects
                })

        # 按类型、部门、总工时排序
        role_priority = {
            'project_manager': 1,
            'data_collection': 2,
            'software_dev': 3,
            'staff': 4
        }
        result.sort(key=lambda x: (
            role_priority.get(x['role'], 99),
            x['deptName'] or '',
            -x['totalHours']
        ))

        return success_response(data=result)

    except Exception as e:
        return error_response(500, str(e), http_status=500)
