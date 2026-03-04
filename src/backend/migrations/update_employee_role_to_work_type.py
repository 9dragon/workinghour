"""
数据迁移：将 employees.role 从旧值迁移为新的 work_type 风格值

迁移规则：
- project_manager → staff（需手动设置具体工时类型）
- data_collection → staff（需手动设置具体工时类型）
- software_dev → staff（需手动设置具体工时类型）
- staff → staff（保持不变）

迁移后，新的 role 值将与 work_hour_data.work_type 保持一致：
- project_delivery: 项目交付
- product_research: 产品研发
- presales_support: 售前支持
- dept_internal: 部门内务
- leave: 请假
- staff: 普通员工（默认值）
"""
from app import create_app
from app.models.db import db
from app.models.employee import Employee


def migrate():
    """执行迁移"""
    app = create_app()
    with app.app_context():
        employees = Employee.query.all()
        count = 0

        for emp in employees:
            old_role = emp.role
            # 将所有非 staff 的角色统一设为 staff
            # 后续可在员工管理中手动设置具体工时类型
            if emp.role not in ['staff', 'project_delivery', 'product_research',
                                'presales_support', 'dept_internal', 'leave']:
                emp.role = 'staff'
                count += 1
                print(f"更新员工 {emp.employee_name}: {old_role} → staff")

        db.session.commit()
        print(f"迁移完成，共更新 {count} 条记录")


if __name__ == '__main__':
    migrate()
