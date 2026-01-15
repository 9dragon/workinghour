"""
工时核对路由
"""
from flask import Blueprint, request
from app.models.db import db
from app.models.work_hour_data import WorkHourData
from app.models.check_record import CheckRecord
from app.models.sys_config import SysConfig
from app.utils.response import success_response, error_response
from app.utils.helpers import calculate_date_range, get_workdays_in_range, generate_batch_no
from sqlalchemy import func
from datetime import datetime, timedelta
import json

check_bp = Blueprint('check', __name__)


@check_bp.route('/check/integrity', methods=['POST'])
def check_integrity():
    """完整性检查"""
    try:
        data = request.get_json()
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        dept_name = data.get('deptName', '').strip()
        user_name = data.get('userName', '').strip()
        workdays = data.get('workdays', [1, 2, 3, 4, 5])

        # 验证日期范围
        is_valid, error_msg, days_count = calculate_date_range(start_date, end_date, max_days=90)
        if not is_valid:
            return error_response(4001, error_msg), 400

        # 获取工作日列表
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        workdays_list = get_workdays_in_range(start, end, workdays)

        total_workdays = len(workdays_list)

        # 构建查询
        query = db.session.query(
            WorkHourData.user_name,
            WorkHourData.dept_name,
            func.count(func.distinct(WorkHourData.work_date)).label('days_count')
        )

        if dept_name:
            query = query.filter(WorkHourData.dept_name.like(f'%{dept_name}%'))

        if user_name:
            query = query.filter(WorkHourData.user_name.like(f'%{user_name}%'))

        query = query.filter(
            WorkHourData.work_date >= start,
            WorkHourData.work_date <= end
        ).group_by(WorkHourData.user_name, WorkHourData.dept_name)

        results = query.all()

        # 生成检查结果
        details = []
        total_missing_days = 0
        abnormal_users = []

        for user_name, dept, days_count in results:
            missing_days = total_workdays - days_count

            if missing_days > 0:
                total_missing_days += missing_days
                abnormal_users.append(user_name)

                # 查找缺失日期
                user_dates = db.session.query(
                    func.distinct(WorkHourData.work_date)
                ).filter(
                    WorkHourData.user_name == user_name,
                    WorkHourData.work_date >= start,
                    WorkHourData.work_date <= end
                ).all()

                user_dates_set = {d[0] for d in user_dates}
                missing_dates = [d for d in workdays_list if d not in user_dates_set]

                details.append({
                    'userName': user_name,
                    'deptName': dept,
                    'actualDays': days_count,
                    'expectedDays': total_workdays,
                    'missingDays': missing_days,
                    'missingDates': [d.strftime('%Y-%m-%d') for d in missing_dates]
                })

        # 计算完整率
        total_users = len(results)
        integrity_users = total_users - len(abnormal_users)
        integrity_rate = (integrity_users / total_users * 100) if total_users > 0 else 100

        # 保存检查记录
        batch_no = generate_batch_no('CHK')
        check_record = CheckRecord(
            batch_no=batch_no,
            check_type='integrity',
            start_date=start,
            end_date=end,
            filters=json.dumps({'deptName': dept_name, 'userName': user_name, 'workdays': workdays}),
            result_summary=json.dumps({
                'totalWorkdays': total_workdays,
                'totalUsers': total_users,
                'abnormalUsers': len(abnormal_users),
                'integrityRate': f"{integrity_rate:.2f}%"
            }),
            check_details=json.dumps(details[:100]),
            check_user=request.current_user.get('userName') if hasattr(request, 'current_user') else 'system'
        )
        db.session.add(check_record)
        db.session.commit()

        return success_response(data={
            'batchNo': batch_no,
            'checkTime': datetime.now().isoformat(),
            'totalWorkdays': total_workdays,
            'totalUsers': total_users,
            'abnormalUsers': abnormal_users,
            'abnormalCount': len(abnormal_users),
            'totalMissingDays': total_missing_days,
            'integrityRate': f"{integrity_rate:.2f}%",
            'list': details[:100]
        })

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@check_bp.route('/check/compliance', methods=['POST'])
def check_compliance():
    """合规性检查"""
    try:
        data = request.get_json()
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        dept_name = data.get('deptName', '').strip()
        user_name = data.get('userName', '').strip()
        standard_hours = data.get('standardHours', 8)
        min_hours = data.get('minHours', 4)
        max_overtime = data.get('maxOvertime', 4)
        max_monthly_overtime = data.get('maxMonthlyOvertime', 80)

        # 验证日期范围
        is_valid, error_msg, _ = calculate_date_range(start_date, end_date, max_days=90)
        if not is_valid:
            return error_response(4001, error_msg), 400

        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        # 构建基础查询
        query = WorkHourData.query

        if dept_name:
            query = query.filter(WorkHourData.dept_name.like(f'%{dept_name}%'))

        if user_name:
            query = query.filter(WorkHourData.user_name.like(f'%{user_name}%'))

        query = query.filter(
            WorkHourData.work_date >= start,
            WorkHourData.work_date <= end
        )

        all_records = query.all()

        # 分析异常数据
        abnormal_users = set()
        invalid_types = {
            'tooLong': [],  # 超过标准时长
            'tooShort': [],  # 低于最小时长
            'excessiveOvertime': [],  # 加班时长超标
            'monthlyOvertimeExceed': []  # 月度加班超标
        }

        details = []

        for record in all_records:
            issues = []

            # 检查工作时长
            if record.work_hours > standard_hours:
                issues.append(f"工作时长{record.work_hours}小时超过标准{standard_hours}小时")
                invalid_types['tooLong'].append(record.user_name)
                abnormal_users.add(record.user_name)

            if record.work_hours < min_hours:
                issues.append(f"工作时长{record.work_hours}小时低于最小{min_hours}小时")
                invalid_types['tooShort'].append(record.user_name)
                abnormal_users.add(record.user_name)

            # 检查加班时长
            if record.overtime_hours > max_overtime:
                issues.append(f"加班时长{record.overtime_hours}小时超过单日限制{max_overtime}小时")
                invalid_types['excessiveOvertime'].append(record.user_name)
                abnormal_users.add(record.user_name)

            if issues:
                details.append({
                    'userName': record.user_name,
                    'deptName': record.dept_name,
                    'workDate': record.work_date.strftime('%Y-%m-%d'),
                    'projectName': record.project_name,
                    'workHours': record.work_hours,
                    'overtimeHours': record.overtime_hours,
                    'issues': issues
                })

        # 检查月度加班超标
        for user in abnormal_users:
            user_records = [r for r in all_records if r.user_name == user]

            # 按月分组
            monthly_overtime = {}
            for record in user_records:
                month_key = record.work_date.strftime('%Y-%m')
                monthly_overtime[month_key] = monthly_overtime.get(month_key, 0) + record.overtime_hours

            for month, total_overtime in monthly_overtime.items():
                if total_overtime > max_monthly_overtime:
                    invalid_types['monthlyOvertimeExceed'].append(f"{user}({month})")
                    # 找到该月有加班记录的日期
                    month_dates = [r.work_date.strftime('%Y-%m-%d') for r in user_records
                                 if r.work_date.strftime('%Y-%m') == month and r.overtime_hours > 0]
                    details.append({
                        'userName': user,
                        'deptName': user_records[0].dept_name,
                        'workDate': month,
                        'projectName': '月度汇总',
                        'workHours': 0,
                        'overtimeHours': total_overtime,
                        'issues': [f"月度加班{total_overtime}小时超过限制{max_monthly_overtime}小时"]
                    })

        # 计算合规率
        total_users = len(set(r.user_name for r in all_records))
        compliance_rate = ((total_users - len(abnormal_users)) / total_users * 100) if total_users > 0 else 100

        # 统计各类型异常人数
        invalid_counts = {
            'tooLong': len(set(invalid_types['tooLong'])),
            'tooShort': len(set(invalid_types['tooShort'])),
            'excessiveOvertime': len(set(invalid_types['excessiveOvertime'])),
            'monthlyOvertimeExceed': len(invalid_types['monthlyOvertimeExceed'])
        }

        # 保存检查记录
        batch_no = generate_batch_no('CHK')
        check_record = CheckRecord(
            batch_no=batch_no,
            check_type='compliance',
            start_date=start,
            end_date=end,
            filters=json.dumps(data),
            result_summary=json.dumps({
                'totalUsers': total_users,
                'abnormalUsers': len(abnormal_users),
                'complianceRate': f"{compliance_rate:.2f}%"
            }),
            check_details=json.dumps(details[:100]),
            check_user=request.current_user.get('userName') if hasattr(request, 'current_user') else 'system'
        )
        db.session.add(check_record)
        db.session.commit()

        return success_response(data={
            'batchNo': batch_no,
            'checkTime': datetime.now().isoformat(),
            'totalUsers': total_users,
            'abnormalUsers': list(abnormal_users),
            'abnormalCount': len(abnormal_users),
            'complianceRate': f"{compliance_rate:.2f}%",
            'invalidTypes': invalid_counts,
            'list': details[:100]
        })

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@check_bp.route('/check/history', methods=['GET'])
def get_check_history():
    """获取核对历史记录"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        check_type = request.args.get('checkType', '')  # 'integrity' or 'compliance'

        query = CheckRecord.query

        if check_type in ['integrity', 'compliance']:
            query = query.filter_by(check_type=check_type)

        pagination = query.order_by(
            CheckRecord.check_time.desc()
        ).paginate(page=page, per_page=size, error_out=False)

        records = [record.to_dict() for record in pagination.items]

        return success_response(data={
            'list': records,
            'total': pagination.total,
            'page': page,
            'size': size,
            'totalPages': pagination.pages
        })

    except Exception as e:
        return error_response(500, str(e)), 500


@check_bp.route('/check/record/<batch_no>', methods=['GET'])
def get_check_detail(batch_no):
    """获取核对记录详情"""
    try:
        record = CheckRecord.query.filter_by(batch_no=batch_no).first()

        if not record:
            return error_response(3001, '核对记录不存在'), 404

        data = record.to_dict()

        # 添加详细信息
        if record.check_details:
            try:
                data['details'] = json.loads(record.check_details)
            except:
                data['details'] = []

        return success_response(data=data)

    except Exception as e:
        return error_response(500, str(e)), 500
