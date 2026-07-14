"""
工时核对路由
"""
from flask import Blueprint, request
from app.models.db import db
from app.models.work_hour_data import WorkHourData
from app.models.check_record import CheckRecord
from app.models.sys_config import SysConfig
from app.models.holiday import Holiday
from app.utils.response import success_response, error_response
from app.utils.helpers import calculate_date_range, get_workdays_in_range, generate_batch_no
from app.services.check_service import run_integrity_check
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
        check_user = request.current_user.get('userName') if hasattr(request, 'current_user') else 'system'

        check_no, summary, details = run_integrity_check(
            start_date=start_date,
            end_date=end_date,
            dept_name=dept_name,
            user_name=user_name,
            workdays=workdays,
            trigger_type=trigger_type,
            check_user=check_user
        )

        return success_response(data={
            'checkNo': check_no,
            'checkTime': datetime.now().isoformat(),
            'summary': summary,
            'list': details[:100]
        })

    except ValueError as e:
        return error_response(4001, str(e), http_status=400)
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

        # 获取所有涉及时间范围内的节假日数据（一次性查询，避免N+1问题）
        all_holiday_records = []
        if start is not None and end is not None:
            all_holiday_records = db.session.query(
                Holiday.holiday_date,
                Holiday.is_workday
            ).filter(
                Holiday.holiday_date >= start,
                Holiday.holiday_date <= end
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

            # 过滤出该工单时间范围内的节假日数据
            non_workdays = [h.holiday_date for h in all_holiday_records if not h.is_workday and start_time <= h.holiday_date <= end_time]
            extra_workdays = [h.holiday_date for h in all_holiday_records if h.is_workday and start_time <= h.holiday_date <= end_time]

            workdays_in_range = get_workdays_in_range(start_time, end_time, [1, 2, 3, 4, 5], non_workdays)
            # 加上调休工作日
            for wd in extra_workdays:
                if wd not in workdays_in_range:
                    workdays_in_range.append(wd)
            workdays_in_range.sort()
            # 从配置中读取标准工作时长
            standard_hours_config = SysConfig.query.filter_by(config_key='check.standard_hours').first()
            standard_hours = int(standard_hours_config.config_value) if standard_hours_config else 8
            legal_work_hours = len(workdays_in_range) * standard_hours

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


@check_bp.route('/check/record/<check_no>', methods=['DELETE'])
def delete_check_record(check_no):
    """删除核对记录"""
    try:
        record = CheckRecord.query.filter_by(check_no=check_no).first()

        if not record:
            return error_response(3001, '核对记录不存在', http_status=404)

        # 如果有关联的报告文件，也需要删除
        if record.report_path:
            import os
            if os.path.exists(record.report_path):
                os.remove(record.report_path)

        db.session.delete(record)
        db.session.commit()

        return success_response(message='删除成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@check_bp.route('/check/records/batch', methods=['DELETE'])
def batch_delete_check_records():
    """批量删除核对记录"""
    try:
        data = request.get_json()
        check_nos = data.get('checkNos', [])

        if not check_nos:
            return error_response(4001, '请选择要删除的记录', http_status=400)

        # 查询要删除的记录
        records = CheckRecord.query.filter(CheckRecord.check_no.in_(check_nos)).all()

        if not records:
            return error_response(3001, '核对记录不存在', http_status=404)

        # 删除关联的报告文件
        import os
        for record in records:
            if record.report_path and os.path.exists(record.report_path):
                os.remove(record.report_path)

        # 批量删除记录
        for record in records:
            db.session.delete(record)

        db.session.commit()

        return success_response(message=f'成功删除 {len(records)} 条记录')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)
