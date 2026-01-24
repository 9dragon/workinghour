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
from sqlalchemy import func, case, and_, or_
from datetime import datetime, timedelta
import json

check_bp = Blueprint('check', __name__)


@check_bp.route('/check/integrity-consistency', methods=['POST'])
def check_integrity_consistency():
    """周报提交完整性和重复检测检查"""
    try:
        data = request.get_json()
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        dept_name = (data.get('deptName') or '').strip() if data.get('deptName') is not None else ''
        user_name = (data.get('userName') or '').strip() if data.get('userName') is not None else ''
        workdays = data.get('workdays', [1, 2, 3, 4, 5])
        trigger_type = data.get('triggerType', 'manual')

        # 验证日期范围（已去除90天限制）
        is_valid, error_msg, days_count, start, end = calculate_date_range(start_date, end_date)
        if not is_valid:
            return error_response(4001, error_msg, http_status=400)

        # 如果 start 和 end 都为 None，表示全量查询，获取数据库中所有数据的日期范围
        if start is None and end is None:
            date_range = db.session.query(
                func.min(WorkHourData.start_time).label('min_date'),
                func.max(WorkHourData.end_time).label('max_date')
            ).first()

            if date_range and date_range.min_date and date_range.max_date:
                start = date_range.min_date
                end = date_range.max_date
            else:
                # 数据库中无数据
                start = datetime.now().date()
                end = datetime.now().date()

        workdays_list = get_workdays_in_range(start, end, workdays)

        # 1. 获取所有需要检查的用户列表
        user_query = db.session.query(
            WorkHourData.user_name,
            WorkHourData.dept_name
        ).distinct()

        if dept_name:
            user_query = user_query.filter(WorkHourData.dept_name.like(f'%{dept_name}%'))

        if user_name:
            user_query = user_query.filter(WorkHourData.user_name.like(f'%{user_name}%'))

        user_list = user_query.all()

        # 生成问题列表
        details = []
        total_missing_days = 0
        total_duplicate_days = 0
        missing_users = []
        duplicate_users = []

        # 2. 对每个用户进行空缺和重复检查
        for user, dept in user_list:
            # 查询该用户的所有工单（去重），按开始时间排序
            user_orders_query = db.session.query(
                WorkHourData.serial_no,
                WorkHourData.start_time,
                WorkHourData.end_time
            ).filter(
                WorkHourData.user_name == user
            )

            # 添加筛选条件
            if dept_name:
                user_orders_query = user_orders_query.filter(WorkHourData.dept_name.like(f'%{dept_name}%'))

            # 筛选在核对时间范围内的工单（工单开始时间在范围内）
            user_orders_query = user_orders_query.filter(
                WorkHourData.start_time <= end,  # 工单开始时间不晚于核对结束时间
                WorkHourData.end_time >= start   # 工单结束时间不早于核对开始时间
            )

            user_orders = user_orders_query.distinct().order_by(WorkHourData.start_time).all()

            if len(user_orders) == 0:
                continue

            # ========== 空缺检查：检查相邻工单之间的时间空隙 ==========
            for i in range(len(user_orders) - 1):
                current_end = user_orders[i].end_time
                next_start = user_orders[i + 1].start_time

                # 如果前一工单结束时间 < 后一工单开始时间，存在空隙
                if current_end < next_start:
                    gap_start = current_end + timedelta(days=1)
                    gap_end = next_start - timedelta(days=1)

                    # 计算空隙期间的工作日天数
                    workdays_in_gap = get_workdays_in_range(gap_start, gap_end, workdays)

                    if len(workdays_in_gap) > 0:
                        total_missing_days += len(workdays_in_gap)
                        if user not in missing_users:
                            missing_users.append(user)

                        details.append({
                            'deptName': dept,
                            'userName': user,
                            'issueType': 'missing',
                            'serialNo': None,
                            'gapStartDate': gap_start.strftime('%Y-%m-%d'),
                            'gapEndDate': gap_end.strftime('%Y-%m-%d'),
                            'affectedWorkdays': len(workdays_in_gap),
                            'description': '未提交周报'
                        })

            # ========== 重复检查：检查工单时间范围是否有重叠 ==========
            for i in range(len(user_orders)):
                for j in range(i + 1, len(user_orders)):
                    order_a = user_orders[i]
                    order_b = user_orders[j]

                    # 检查时间范围是否重叠
                    # 重叠条件：order_a.start_time < order_b.end_time AND order_a.end_time > order_b.start_time
                    # 注意：连续的工单（如 12-01至12-07 和 12-08至12-14）不算重叠
                    if order_a.start_time < order_b.end_time and order_a.end_time > order_b.start_time:
                        # 计算重叠期间
                        overlap_start = max(order_a.start_time, order_b.start_time)
                        overlap_end = min(order_a.end_time, order_b.end_time)

                        # 计算重叠期间的工作日天数
                        workdays_in_overlap = get_workdays_in_range(overlap_start, overlap_end, workdays)

                        if len(workdays_in_overlap) > 0:
                            total_duplicate_days += len(workdays_in_overlap)
                            if user not in duplicate_users:
                                duplicate_users.append(user)

                            details.append({
                                'deptName': dept,
                                'userName': user,
                                'issueType': 'duplicate',
                                'serialNo': f'{order_a.serial_no},{order_b.serial_no}',
                                'gapStartDate': overlap_start.strftime('%Y-%m-%d'),
                                'gapEndDate': overlap_end.strftime('%Y-%m-%d'),
                                'affectedWorkdays': len(workdays_in_overlap),
                                'description': f'与序号{order_b.serial_no}时间重叠'
                            })

        # 计算完整性百分比
        total_users = len(user_list)
        integrity_users = total_users - len(missing_users)
        integrity_rate = (integrity_users / total_users * 100) if total_users > 0 else 100

        # 保存检查记录（包含详细列表）
        check_no = generate_batch_no('CHK')
        check_record = CheckRecord(
            check_no=check_no,
            check_type='integrity-consistency',
            trigger_type=trigger_type,
            start_date=start,
            end_date=end,
            dept_name=dept_name if dept_name else None,
            user_name=user_name if user_name else None,
            check_config=json.dumps({'deptName': dept_name, 'userName': user_name, 'workdays': workdays}),
            check_result=json.dumps({
                'totalUsers': total_users,
                'missingUsers': len(missing_users),
                'totalMissingWorkdays': total_missing_days,
                'duplicateUsers': len(duplicate_users),
                'totalDuplicateWorkdays': total_duplicate_days,
                'integrityRate': f"{integrity_rate:.2f}%"
            }),
            check_details=json.dumps(details),  # 保存完整详细列表
            check_user=request.current_user.get('userName') if hasattr(request, 'current_user') else 'system'
        )
        db.session.add(check_record)
        db.session.commit()

        return success_response(data={
            'checkNo': check_no,
            'checkTime': datetime.now().isoformat(),
            'summary': {
                'totalUsers': total_users,
                'missingUsers': len(missing_users),
                'totalMissingWorkdays': total_missing_days,
                'duplicateUsers': len(duplicate_users),
                'totalDuplicateWorkdays': total_duplicate_days,
                'integrityRate': integrity_rate
            },
            'list': details[:100]
        })

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@check_bp.route('/check/work-hours-consistency', methods=['POST'])
def check_work_hours_consistency():
    """工作时长一致性检查（按工单聚合统计）"""
    try:
        data = request.get_json()
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        dept_name = (data.get('deptName') or '').strip() if data.get('deptName') is not None else ''
        user_name = (data.get('userName') or '').strip() if data.get('userName') is not None else ''
        trigger_type = data.get('triggerType', 'manual')

        # 验证日期范围（已去除90天限制）
        is_valid, error_msg, days_count, start, end = calculate_date_range(start_date, end_date)
        if not is_valid:
            return error_response(4001, error_msg, http_status=400)

        # 如果 start 和 end 都为 None，表示全量查询
        if start is None and end is None:
            # 不添加时间范围过滤条件，查询所有数据
            time_filter = False
        else:
            time_filter = True

        # 构建基础查询
        base_query = WorkHourData.query

        if dept_name:
            base_query = base_query.filter(WorkHourData.dept_name.like(f'%{dept_name}%'))

        if user_name:
            base_query = base_query.filter(WorkHourData.user_name.like(f'%{user_name}%'))

        if time_filter:
            base_query = base_query.filter(
                WorkHourData.start_time >= start,
                WorkHourData.end_time <= end
            )

        all_records = base_query.all()

        # 按serial_no聚合统计每种工作类型的时长
        serial_stats = db.session.query(
            WorkHourData.serial_no,
            WorkHourData.user_name,
            WorkHourData.start_time,
            WorkHourData.end_time,
            func.sum(case((WorkHourData.work_type == 'project_delivery', WorkHourData.work_hours), else_=0)).label('project_delivery_hours'),
            func.sum(case((WorkHourData.work_type == 'product_research', WorkHourData.work_hours), else_=0)).label('product_research_hours'),
            func.sum(case((WorkHourData.work_type == 'presales_support', WorkHourData.work_hours), else_=0)).label('presales_support_hours'),
            func.sum(case((WorkHourData.work_type == 'dept_internal', WorkHourData.work_hours), else_=0)).label('dept_internal_hours'),
            func.sum(WorkHourData.work_hours).label('total_work_hours'),
            func.sum(WorkHourData.leave_hours).label('total_leave_hours')
        )

        if time_filter:
            serial_stats = serial_stats.filter(
                WorkHourData.start_time >= start,
                WorkHourData.end_time <= end
            )

        if dept_name:
            serial_stats = serial_stats.filter(WorkHourData.dept_name.like(f'%{dept_name}%'))

        if user_name:
            serial_stats = serial_stats.filter(WorkHourData.user_name.like(f'%{user_name}%'))

        serial_stats = serial_stats.group_by(
            WorkHourData.serial_no,
            WorkHourData.user_name,
            WorkHourData.start_time,
            WorkHourData.end_time
        ).all()

        # 计算每个工单的应工作时长（考虑法定工作日）
        details = []
        total_serials = 0
        normal_serials = 0
        short_serials = 0
        excess_serials = 0

        work_type_totals = {
            'project_delivery': 0,
            'product_research': 0,
            'presales_support': 0,
            'dept_internal': 0
        }

        work_type_counts = {
            'project_delivery': 0,
            'product_research': 0,
            'presales_support': 0,
            'dept_internal': 0
        }

        for serial_no, user, start_time, end_time, pd_hours, pr_hours, ps_hours, di_hours, total_wh, leave_h in serial_stats:
            # 计算该工单时间范围内的法定工作日数
            actual_days = (end_time - start_time).days + 1
            workdays_in_range = get_workdays_in_range(start_time, end_time, [1, 2, 3, 4, 5])
            legal_work_hours = len(workdays_in_range) * 8

            # 实际工作时长 = 各类型工作时长之和
            actual_work_hours = (pd_hours or 0) + (pr_hours or 0) + (ps_hours or 0) + (di_hours or 0)
            total_work_hours = actual_work_hours + (leave_h or 0)

            # 应工作时长 = 法定工作时间
            expected_work_hours = legal_work_hours

            # 计算差值
            difference = total_work_hours - expected_work_hours

            # 判断状态
            if difference == 0:
                status = 'normal'
                normal_serials += 1
            elif difference < 0:
                status = 'short'
                short_serials += 1
            else:
                status = 'excess'
                excess_serials += 1

            total_serials += 1

            # 统计各工作类型时长
            if pd_hours and pd_hours > 0:
                work_type_totals['project_delivery'] += pd_hours
                work_type_counts['project_delivery'] += 1
            if pr_hours and pr_hours > 0:
                work_type_totals['product_research'] += pr_hours
                work_type_counts['product_research'] += 1
            if ps_hours and ps_hours > 0:
                work_type_totals['presales_support'] += ps_hours
                work_type_counts['presales_support'] += 1
            if di_hours and di_hours > 0:
                work_type_totals['dept_internal'] += di_hours
                work_type_counts['dept_internal'] += 1

            # 只添加异常记录到详情列表
            if status != 'normal':
                details.append({
                    'serialNo': serial_no,
                    'userName': user,
                    'startTime': start_time.strftime('%Y-%m-%d'),
                    'endTime': end_time.strftime('%Y-%m-%d'),
                    'projectDeliveryHours': round(pd_hours or 0, 2),
                    'productResearchHours': round(pr_hours or 0, 2),
                    'presalesSupportHours': round(ps_hours or 0, 2),
                    'deptInternalHours': round(di_hours or 0, 2),
                    'totalWorkHours': round(total_work_hours, 2),
                    'leaveHours': round(leave_h or 0, 2),
                    'expectedWorkHours': round(expected_work_hours, 2),
                    'legalWorkHours': round(legal_work_hours, 2),
                    'difference': round(difference, 2),
                    'status': status
                })

        # 计算合规率
        compliance_rate = (normal_serials / total_serials * 100) if total_serials > 0 else 100

        # 计算各工作类型平均时长
        work_type_stats = {}
        for work_type in ['project_delivery', 'product_research', 'presales_support', 'dept_internal']:
            total_hours = work_type_totals[work_type]
            count = work_type_counts[work_type]
            work_type_stats[work_type] = {
                'totalHours': round(total_hours, 2),
                'avgHours': round(total_hours / count, 2) if count > 0 else 0
            }

        # 保存检查记录（包含详细列表）
        check_no = generate_batch_no('CHK')
        check_record = CheckRecord(
            check_no=check_no,
            check_type='work-hours-consistency',
            trigger_type=trigger_type,
            start_date=start,
            end_date=end,
            dept_name=dept_name if dept_name else None,
            user_name=user_name if user_name else None,
            check_config=json.dumps(data),
            check_result=json.dumps({
                'totalSerials': total_serials,
                'normalSerials': normal_serials,
                'shortSerials': short_serials,
                'excessSerials': excess_serials,
                'complianceRate': f"{compliance_rate:.2f}%"
            }),
            check_details=json.dumps(details),  # 保存完整详细列表
            check_user=request.current_user.get('userName') if hasattr(request, 'current_user') else 'system'
        )
        db.session.add(check_record)
        db.session.commit()

        return success_response(data={
            'checkNo': check_no,
            'checkTime': datetime.now().isoformat(),
            'summary': {
                'totalSerials': total_serials,
                'normalSerials': normal_serials,
                'shortSerials': short_serials,
                'excessSerials': excess_serials,
                'complianceRate': compliance_rate,
                'workTypeStats': work_type_stats
            },
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
        check_type = request.args.get('checkType', '')

        query = CheckRecord.query

        if check_type in ['integrity', 'integrity-consistency', 'compliance', 'work-hours-consistency']:
            query = query.filter_by(check_type=check_type)

        pagination = query.order_by(
            CheckRecord.check_time.desc()
        ).paginate(page=page, per_page=size, error_out=False)

        records = []
        for record in pagination.items:
            record_dict = record.to_dict()
            # 添加checkResult字段用于前端显示
            if record.check_result:
                try:
                    record_dict['checkResult'] = json.loads(record.check_result)
                except:
                    record_dict['checkResult'] = None
            records.append(record_dict)

        return success_response(data={
            'list': records,
            'total': pagination.total,
            'page': page,
            'size': size,
            'totalPages': pagination.pages
        })

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@check_bp.route('/check/record/<check_no>', methods=['GET'])
def get_check_detail(check_no):
    """获取核对记录详情"""
    try:
        record = CheckRecord.query.filter_by(check_no=check_no).first()

        if not record:
            return error_response(3001, '核对记录不存在', http_status=404)

        data = record.to_dict()

        # 添加详细信息
        if record.check_result:
            try:
                data['checkResult'] = json.loads(record.check_result)
            except:
                data['checkResult'] = None

        # 读取详细列表数据
        if record.check_details:
            try:
                data['list'] = json.loads(record.check_details)
            except:
                data['list'] = []
        else:
            data['list'] = []

        return success_response(data=data)

    except Exception as e:
        return error_response(500, str(e), http_status=500)
