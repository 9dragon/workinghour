"""
工时查询路由
"""
from flask import Blueprint, request, send_file
from sqlalchemy import func
from app.models.db import db
from app.models.work_hour_data import WorkHourData
from app.models.import_record import ImportRecord
from app.utils.response import success_response, error_response, paginated_response
from app.utils.helpers import calculate_date_range
from app.utils.jwt_utils import auth_required
import pandas as pd
from datetime import datetime
from io import BytesIO
import os

query_bp = Blueprint('query', __name__)


def _refresh_import_record_stats(batch_nos):
    """删除工时后重算受影响批次的 success_rows。

    total_rows/repeat_rows/invalid_rows 是导入时的历史快照，不动；
    success_rows 是实际入库行数，删除后用 COUNT(*) 重新统计覆盖写入。
    """
    if not batch_nos:
        return
    for batch_no in set(batch_nos):
        if not batch_no:
            continue
        cnt = db.session.query(func.count(WorkHourData.id)) \
            .filter(WorkHourData.import_batch_no == batch_no).scalar() or 0
        rec = ImportRecord.query.filter_by(batch_no=batch_no).first()
        if rec:
            rec.success_rows = cnt


@query_bp.route('/query/project', methods=['GET'])
def query_by_project():
    """按项目维度查询工时数据"""
    try:
        # 获取查询参数
        project_name = request.args.get('projectName', '').strip()
        project_manager = request.args.get('projectManager', '').strip()
        user_name = request.args.get('userName', '').strip()
        start_date = request.args.get('startDate', '').strip()
        end_date = request.args.get('endDate', '').strip()
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        sort_by = request.args.get('sortBy', 'start_time')
        sort_order = request.args.get('sortOrder', 'desc')

        # 构建查询
        query = WorkHourData.query

        # 只查询项目交付和产品研发类工时
        query = query.filter(WorkHourData.work_type.in_(['project_delivery', 'product_research']))

        if project_name:
            query = query.filter(WorkHourData.project_name.like(f'%{project_name}%'))

        if project_manager:
            query = query.filter(WorkHourData.project_manager.like(f'%{project_manager}%'))

        if user_name:
            query = query.filter(WorkHourData.user_name.like(f'%{user_name}%'))

        if start_date and end_date:
            # 验证日期范围
            is_valid, error_msg, *_ = calculate_date_range(start_date, end_date)
            if not is_valid:
                return error_response(4001, error_msg), 400

            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            # 完全包含逻辑：工时记录的开始时间和结束时间都必须在查询范围内
            query = query.filter(WorkHourData.start_time >= start, WorkHourData.end_time <= end)

        # 计算统计数据（在分页前）
        stats = query.with_entities(
            func.count(WorkHourData.id).label('total'),
            func.sum(WorkHourData.work_hours).label('total_work_hours'),
            func.sum(WorkHourData.overtime_hours).label('total_overtime_hours')
        ).first()

        # 统计项目数和人员数
        project_count = query.with_entities(
            func.count(func.distinct(WorkHourData.project_name))
        ).scalar()

        user_count = query.with_entities(
            func.count(func.distinct(WorkHourData.user_name))
        ).scalar()

        # 排序
        order_col = getattr(WorkHourData, sort_by, WorkHourData.start_time)
        if sort_order == 'desc':
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

        # 分页
        pagination = query.paginate(page=page, per_page=size, error_out=False)

        data_list = [item.to_dict() for item in pagination.items]

        return success_response(data={
            'list': data_list,
            'total': pagination.total,
            'page': page,
            'size': size,
            'totalPages': pagination.pages,
            'summary': {
                'projectCount': project_count or 0,
                'userCount': user_count or 0,
                'totalWorkHours': float(stats.total_work_hours or 0),
                'totalOvertimeHours': float(stats.total_overtime_hours or 0)
            }
        })

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@query_bp.route('/query/organization', methods=['GET'])
def query_by_organization():
    """按组织维度查询工时数据"""
    try:
        # 获取查询参数
        dept_name = request.args.get('deptName', '').strip()
        user_name = request.args.get('userName', '').strip()
        project_name = request.args.get('projectName', '').strip()
        start_date = request.args.get('startDate', '').strip()
        end_date = request.args.get('endDate', '').strip()
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        sort_by = request.args.get('sortBy', 'start_time')
        sort_order = request.args.get('sortOrder', 'desc')

        # 构建查询
        query = WorkHourData.query

        if dept_name:
            query = query.filter(WorkHourData.dept_name.like(f'%{dept_name}%'))

        if user_name:
            query = query.filter(WorkHourData.user_name.like(f'%{user_name}%'))

        if project_name:
            query = query.filter(WorkHourData.project_name.like(f'%{project_name}%'))

        if start_date and end_date:
            # 验证日期范围
            is_valid, error_msg, *_ = calculate_date_range(start_date, end_date)
            if not is_valid:
                return error_response(4001, error_msg), 400

            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            # 完全包含逻辑：工时记录的开始时间和结束时间都必须在查询范围内
            query = query.filter(WorkHourData.start_time >= start, WorkHourData.end_time <= end)

        # 计算统计数据（在分页前）
        stats = query.with_entities(
            func.count(WorkHourData.id).label('total'),
            func.sum(WorkHourData.work_hours).label('total_work_hours'),
            func.sum(WorkHourData.overtime_hours).label('total_overtime_hours')
        ).first()

        # 统计部门数和人员数
        dept_count = query.with_entities(
            func.count(func.distinct(WorkHourData.dept_name))
        ).scalar()

        user_count = query.with_entities(
            func.count(func.distinct(WorkHourData.user_name))
        ).scalar()

        # 排序
        order_col = getattr(WorkHourData, sort_by, WorkHourData.start_time)
        if sort_order == 'desc':
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

        # 分页
        pagination = query.paginate(page=page, per_page=size, error_out=False)

        data_list = [item.to_dict() for item in pagination.items]

        return success_response(data={
            'list': data_list,
            'total': pagination.total,
            'page': page,
            'size': size,
            'totalPages': pagination.pages,
            'summary': {
                'deptCount': dept_count or 0,
                'userCount': user_count or 0,
                'totalWorkHours': float(stats.total_work_hours or 0),
                'totalOvertimeHours': float(stats.total_overtime_hours or 0)
            }
        })

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@query_bp.route('/query/export', methods=['POST'])
def export_query_result():
    """导出查询结果为Excel"""
    try:
        data = request.get_json()
        query_type = data.get('queryType')  # 'project' or 'organization'
        filters = data.get('filters', {})

        # 构建查询
        query = WorkHourData.query

        if query_type == 'project':
            if filters.get('projectName'):
                query = query.filter(WorkHourData.project_name.like(f"%{filters['projectName']}%"))
            if filters.get('projectManager'):
                query = query.filter(WorkHourData.project_manager.like(f"%{filters['projectManager']}%"))
            if filters.get('userName'):
                query = query.filter(WorkHourData.user_name.like(f"%{filters['userName']}%"))
        else:  # organization
            if filters.get('deptName'):
                query = query.filter(WorkHourData.dept_name.like(f"%{filters['deptName']}%"))
            if filters.get('userName'):
                query = query.filter(WorkHourData.user_name.like(f"%{filters['userName']}%"))
            if filters.get('projectName'):
                query = query.filter(WorkHourData.project_name.like(f"%{filters['projectName']}%"))

        # 日期过滤
        if filters.get('startDate') and filters.get('endDate'):
            start = datetime.strptime(filters['startDate'], '%Y-%m-%d').date()
            end = datetime.strptime(filters['endDate'], '%Y-%m-%d').date()
            query = query.filter(WorkHourData.start_time >= start, WorkHourData.start_time <= end)

        # 获取所有结果
        results = query.all()

        # 生成Excel
        df = pd.DataFrame([item.to_dict() for item in results])

        # 重排列顺序
        column_order = ['serial_no', 'user_name', 'start_time', 'end_time',
                       'project_name', 'work_hours', 'overtime_hours',
                       'approval_result', 'approval_status', 'project_manager',
                       'dept_name', 'work_date', 'import_batch_no']

        df = df.reindex(columns=column_order)

        # 重命名列
        df.columns = ['序号', '姓名', '开始时间', '结束时间', '项目名称',
                     '工作时长', '加班时长', '审批结果', '审批状态',
                     '项目经理', '部门', '工作日期', '导入批次']

        # 生成文件
        output = BytesIO()
        dimension = '项目维度' if query_type == 'project' else '组织维度'
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f'工时查询结果_{dimension}_{timestamp}.xlsx'

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='工时数据')

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@query_bp.route('/query/work-hour/<int:record_id>', methods=['DELETE'])
@auth_required
def delete_work_hour(record_id):
    """删除单条工时记录"""
    try:
        record = WorkHourData.query.get(record_id)
        if not record:
            return error_response(3001, '工时记录不存在', http_status=404)

        batch_no = record.import_batch_no
        db.session.delete(record)
        db.session.flush()
        _refresh_import_record_stats([batch_no])
        db.session.commit()

        return success_response(message='删除成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@query_bp.route('/query/work-hour/batch', methods=['DELETE'])
@auth_required
def batch_delete_work_hours():
    """批量删除工时记录"""
    try:
        data = request.get_json() or {}
        ids = data.get('ids', [])

        if not ids:
            return error_response(4001, '请选择要删除的记录', http_status=400)
        if len(ids) > 500:
            return error_response(4002, '单次最多删除 500 条', http_status=400)

        records = WorkHourData.query.filter(WorkHourData.id.in_(ids)).all()
        if not records:
            return error_response(3001, '工时记录不存在', http_status=404)

        batch_nos = [r.import_batch_no for r in records]
        for r in records:
            db.session.delete(r)
        db.session.flush()
        _refresh_import_record_stats(batch_nos)
        db.session.commit()

        return success_response(
            message=f'成功删除 {len(records)} 条记录',
            data={'count': len(records)}
        )

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)
