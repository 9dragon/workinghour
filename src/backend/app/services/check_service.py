"""
周报提交完整性检查的核心算法。

抽出为独立模块，便于：
- HTTP handler（routes/check.py）调用
- 调度器（scheduler.py）调用，无需 HTTP 上下文
"""
import json
from datetime import datetime, timedelta

from sqlalchemy import func

from app.models.db import db
from app.models.work_hour_data import WorkHourData
from app.models.check_record import CheckRecord
from app.models.holiday import Holiday
from app.utils.helpers import calculate_date_range, get_workdays_in_range, generate_batch_no


def _collect_missing_in_gap(details, missing_users, user, dept, gap_start, gap_end,
                            workdays, non_workdays, extra_workdays):
    """统计 [gap_start, gap_end] 内的工作日，写入一条 missing 详情；返回工作日数。"""
    if gap_start > gap_end:
        return 0
    workdays_in_gap = get_workdays_in_range(gap_start, gap_end, workdays, non_workdays)
    for wd in extra_workdays:
        if gap_start <= wd <= gap_end and wd not in workdays_in_gap:
            workdays_in_gap.append(wd)
    workdays_in_gap.sort()
    if not workdays_in_gap:
        return 0
    missing_dates = [d.strftime('%Y-%m-%d') for d in workdays_in_gap]
    details.append({
        'deptName': dept,
        'userName': user,
        'issueType': 'missing',
        'serialNo': None,
        'gapStartDate': gap_start.strftime('%Y-%m-%d'),
        'gapEndDate': gap_end.strftime('%Y-%m-%d'),
        'affectedWorkdays': len(workdays_in_gap),
        'missingDates': missing_dates,
        'description': f'未提交周报（{len(workdays_in_gap)}个工作日：{", ".join(missing_dates)}）'
    })
    if user not in missing_users:
        missing_users.append(user)
    return len(workdays_in_gap)


def run_integrity_check(*, start_date, end_date, dept_name='', user_name='',
                        workdays=None, trigger_type='manual', check_user='system'):
    """执行完整性 + 重复检查。

    参数：
        start_date: 'YYYY-MM-DD' 字符串或 None（None 表示全量查询）
        end_date:   'YYYY-MM-DD' 字符串或 None
        dept_name:  部门模糊匹配，空串表示不过滤
        user_name:  姓名模糊匹配，空串表示不过滤
        workdays:   工作日列表，默认 [1,2,3,4,5]
        trigger_type: 'manual' / 'scheduled' / 'import'
        check_user:  触发者标识，定时任务传 'system'

    返回：
        (check_no, summary_dict, details_list)

    异常：
        ValueError: 当日期格式错误或 start > end
    """
    if workdays is None:
        workdays = [1, 2, 3, 4, 5]

    is_valid, error_msg, _, start, end = calculate_date_range(start_date, end_date)
    if not is_valid:
        raise ValueError(error_msg)

    # 全量查询：用数据库中实际数据范围
    if start is None and end is None:
        date_range = db.session.query(
            func.min(WorkHourData.start_time).label('min_date'),
            func.max(WorkHourData.end_time).label('max_date')
        ).first()
        if date_range and date_range.min_date and date_range.max_date:
            start = date_range.min_date
            end = date_range.max_date
        else:
            start = datetime.now().date()
            end = datetime.now().date()

    # 节假日数据
    holiday_records = db.session.query(
        Holiday.holiday_date, Holiday.is_workday
    ).filter(
        Holiday.holiday_date >= start,
        Holiday.holiday_date <= end
    ).all()
    non_workdays = [h.holiday_date for h in holiday_records if not h.is_workday]
    extra_workdays = [h.holiday_date for h in holiday_records if h.is_workday]

    # 应提交名单
    user_query = db.session.query(
        WorkHourData.user_name, WorkHourData.dept_name
    ).distinct()
    if dept_name:
        user_query = user_query.filter(WorkHourData.dept_name.like(f'%{dept_name}%'))
    if user_name:
        user_query = user_query.filter(WorkHourData.user_name.like(f'%{user_name}%'))
    user_list = user_query.all()

    details = []
    total_missing_days = 0
    total_duplicate_days = 0
    missing_users = []
    duplicate_users = []

    for user, dept in user_list:
        user_orders_query = db.session.query(
            WorkHourData.serial_no,
            WorkHourData.start_time,
            WorkHourData.end_time
        ).filter(WorkHourData.user_name == user)

        if dept_name:
            user_orders_query = user_orders_query.filter(WorkHourData.dept_name.like(f'%{dept_name}%'))

        user_orders_query = user_orders_query.filter(
            WorkHourData.start_time <= end,
            WorkHourData.end_time >= start
        )
        user_orders = user_orders_query.distinct().order_by(WorkHourData.start_time).all()

        # Bug 1 场景 B：本次核对区间内无任何工单 → 整段视为空缺
        if len(user_orders) == 0:
            total_missing_days += _collect_missing_in_gap(
                details, missing_users, user, dept,
                start, end, workdays, non_workdays, extra_workdays
            )
            continue

        # Bug 2 首段
        first_order = user_orders[0]
        if first_order.start_time > start:
            total_missing_days += _collect_missing_in_gap(
                details, missing_users, user, dept,
                start, first_order.start_time - timedelta(days=1),
                workdays, non_workdays, extra_workdays
            )

        # 相邻工单空隙
        for i in range(len(user_orders) - 1):
            current_end = user_orders[i].end_time
            next_start = user_orders[i + 1].start_time
            if current_end < next_start:
                gap_start = current_end + timedelta(days=1)
                gap_end = next_start - timedelta(days=1)
                total_missing_days += _collect_missing_in_gap(
                    details, missing_users, user, dept,
                    gap_start, gap_end,
                    workdays, non_workdays, extra_workdays
                )

        # Bug 2 尾段
        last_order = user_orders[-1]
        if last_order.end_time < end:
            total_missing_days += _collect_missing_in_gap(
                details, missing_users, user, dept,
                last_order.end_time + timedelta(days=1), end,
                workdays, non_workdays, extra_workdays
            )

        # 重复检查
        recorded_periods = set()
        for i in range(len(user_orders)):
            for j in range(i + 1, len(user_orders)):
                order_a = user_orders[i]
                order_b = user_orders[j]
                if order_a.start_time < order_b.end_time and order_a.end_time > order_b.start_time:
                    overlap_start = max(order_a.start_time, order_b.start_time)
                    overlap_end = min(order_a.end_time, order_b.end_time)
                    workdays_in_overlap = get_workdays_in_range(
                        overlap_start, overlap_end, workdays, non_workdays
                    )
                    for wd in extra_workdays:
                        if overlap_start <= wd <= overlap_end and wd not in workdays_in_overlap:
                            workdays_in_overlap.append(wd)
                    workdays_in_overlap.sort()
                    if workdays_in_overlap:
                        gap_start_str = overlap_start.strftime('%Y-%m-%d')
                        gap_end_str = overlap_end.strftime('%Y-%m-%d')
                        period_key = (user, gap_start_str, gap_end_str)
                        if period_key not in recorded_periods:
                            recorded_periods.add(period_key)
                            total_duplicate_days += len(workdays_in_overlap)
                            if user not in duplicate_users:
                                duplicate_users.append(user)
                            details.append({
                                'deptName': dept,
                                'userName': user,
                                'issueType': 'duplicate',
                                'serialNo': f'{order_a.serial_no},{order_b.serial_no}',
                                'gapStartDate': gap_start_str,
                                'gapEndDate': gap_end_str,
                                'affectedWorkdays': len(workdays_in_overlap),
                                'description': f'与序号{order_b.serial_no}时间重叠'
                            })

    total_users = len(user_list)
    integrity_users = total_users - len(missing_users)
    integrity_rate = (integrity_users / total_users * 100) if total_users > 0 else 100

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
        check_details=json.dumps(details),
        check_user=check_user
    )
    db.session.add(check_record)
    db.session.commit()

    summary = {
        'totalUsers': total_users,
        'missingUsers': len(missing_users),
        'totalMissingWorkdays': total_missing_days,
        'duplicateUsers': len(duplicate_users),
        'totalDuplicateWorkdays': total_duplicate_days,
        'integrityRate': integrity_rate
    }
    return check_no, summary, details
