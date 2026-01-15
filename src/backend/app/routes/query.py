"""
工时查询路由
"""
from flask import Blueprint, request, send_file
from app.models.db import db
from app.models.work_hour_data import WorkHourData
from app.utils.response import success_response, error_response, paginated_response
from app.utils.helpers import calculate_date_range
import pandas as pd
from datetime import datetime
from io import BytesIO
import os

query_bp = Blueprint('query', __name__)


@query_bp.route('/query/project', methods=['GET'])
def query_by_project():
    """按项目维度查询工时数据"""
    try:
        # 获取查询参数
        project_name = request.args.get('projectName', '').strip()
        project_manager = request.args.get('projectManager', '').strip()
        start_date = request.args.get('startDate', '').strip()
        end_date = request.args.get('endDate', '').strip()
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        sort_by = request.args.get('sortBy', 'start_time')
        sort_order = request.args.get('sortOrder', 'desc')

        # 构建查询
        query = WorkHourData.query

        if project_name:
            query = query.filter(WorkHourData.project_name.like(f'%{project_name}%'))

        if project_manager:
            query = query.filter(WorkHourData.project_manager.like(f'%{project_manager}%'))

        if start_date and end_date:
            # 验证日期范围
            is_valid, error_msg, _ = calculate_date_range(start_date, end_date, max_days=90)
            if not is_valid:
                return error_response(4001, error_msg), 400

            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(WorkHourData.start_time >= start, WorkHourData.start_time <= end)

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
            'totalPages': pagination.pages
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

        if start_date and end_date:
            # 验证日期范围
            is_valid, error_msg, _ = calculate_date_range(start_date, end_date, max_days=90)
            if not is_valid:
                return error_response(4001, error_msg), 400

            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(WorkHourData.start_time >= start, WorkHourData.start_time <= end)

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
            'totalPages': pagination.pages
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
        else:  # organization
            if filters.get('deptName'):
                query = query.filter(WorkHourData.dept_name.like(f"%{filters['deptName']}%"))
            if filters.get('userName'):
                query = query.filter(WorkHourData.user_name.like(f"%{filters['userName']}%"))

        # 日期过滤
        if filters.get('startDate') and filters.get('endDate'):
            start = datetime.strptime(filters['startDate'], '%Y-%m-%d')
            end = datetime.strptime(filters['endDate'], '%Y-%m-%d').replace(hour=23, minute=59, second=59)
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
