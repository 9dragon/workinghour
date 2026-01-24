"""
数据导入路由
"""
from flask import Blueprint, request, current_app
from werkzeug.utils import secure_filename
from app.models.db import db
from app.models.work_hour_data import WorkHourData
from app.models.import_record import ImportRecord
from app.models.sys_config import SysConfig
from app.utils.response import success_response, error_response
from app.utils.jwt_utils import auth_required
from app.utils.helpers import (
    generate_batch_no, validate_excel_file, read_excel_data,
    validate_work_hour_row, calculate_date_range
)
import os
from datetime import datetime
import pandas as pd

import_bp = Blueprint('import', __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}


def allowed_file(filename):
    """检查文件扩展名"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def split_work_types(row, serial_no, user_name, start_time, end_time,
                     batch_no, approval_result, approval_status):
    """
    将一行Excel数据拆分为多条工时记录

    参数:
        row: Excel行数据
        serial_no: 工单序号
        user_name: 用户姓名
        start_time: 开始时间(date)
        end_time: 结束时间(date)
        batch_no: 导入批次号
        approval_result: 审批结果
        approval_status: 审批状态

    返回: (records_list, created_count)
        records_list: 创建的记录列表
        created_count: 创建的记录数量
    """
    records = []

    # 获取部门信息（所有记录共用）
    dept_name = str(row.get('部门', '')).strip() if pd.notna(row.get('部门')) else ''

    # 定义4种工时类型的字段映射
    work_types = [
        {
            'type': 'project_delivery',
            'prefix': '项目交付-',
            'name_field': '项目交付-项目名称',
            'hours_field': '项目交付-工作时长',
            'overtime_field': '项目交付-加班时长',
            'content_field': '项目交付-工作内容',
            'manager_field': '项目交付-项目经理'
        },
        {
            'type': 'product_research',
            'prefix': '产品-',
            'name_field': '产品-项目名称',
            'hours_field': '产品-工作时长',
            'overtime_field': '产品-加班时长',
            'content_field': '产品-工作内容',
            'manager_field': '产品-项目经理'
        },
        {
            'type': 'presales_support',
            'prefix': '售前-',
            'name_field': '售前-项目名称',
            'hours_field': '售前-工作时长',
            'overtime_field': '售前-加班时长',
            'content_field': '售前-工作内容',
            'manager_field': '售前-项目经理'
        },
        {
            'type': 'dept_internal',
            'prefix': '部门-',
            'name_field': '部门-项目名称',
            'hours_field': '部门-工作时长',
            'overtime_field': '部门-加班时长',
            'content_field': '部门-工作内容',
            'manager_field': '部门-项目经理'
        }
    ]

    created_count = 0

    for wt in work_types:
        # 获取该类型的工作时长
        hours_val = row.get(wt['hours_field'], 0)
        work_hours = 0.0 if (pd.isna(hours_val) or hours_val == '') else float(hours_val)

        # 获取加班时长
        overtime_val = row.get(wt['overtime_field'], 0)
        overtime_hours = 0.0 if (pd.isna(overtime_val) or overtime_val == '') else float(overtime_val)

        # 获取项目名称
        project_name = str(row.get(wt['name_field'], '')).strip() if pd.notna(row.get(wt['name_field'])) else ''

        # 创建条件：必须有工作时长或加班时长（避免创建空记录）
        if work_hours > 0 or overtime_hours > 0:
            # 获取工作内容
            work_content = str(row.get(wt['content_field'], '')).strip() if pd.notna(row.get(wt['content_field'])) else ''

            # 获取项目经理
            project_manager = str(row.get(wt['manager_field'], '')).strip() if pd.notna(row.get(wt['manager_field'])) else ''

            # 创建记录
            record = WorkHourData(
                serial_no=serial_no,
                user_name=user_name,
                start_time=start_time,
                end_time=end_time,
                work_type=wt['type'],
                project_name=project_name if project_name else f"{wt['prefix'].replace('-', '')}工时",
                project_manager=project_manager,
                work_hours=work_hours,
                overtime_hours=overtime_hours,
                work_content=work_content,
                approval_result=approval_result,
                approval_status=approval_status,
                dept_name=dept_name,
                import_batch_no=batch_no
            )
            records.append(record)
            created_count += 1

    # 处理请假记录（支持多种列名格式）
    # 尝试多种可能的列名
    leave_hours_candidates = ['请假-请假时长', '请假时长']

    leave_hours_val = None
    for candidate in leave_hours_candidates:
        if candidate in row.index:
            leave_hours_val = row.get(candidate, None)
            break

    # 只有当列存在且有值时才处理
    if leave_hours_val is not None:
        leave_hours = 0.0 if (pd.isna(leave_hours_val) or leave_hours_val == '') else float(leave_hours_val)

        # 同样处理请假类别
        leave_type_candidates = ['请假-请假类别', '请假类别']

        leave_type = ''
        for candidate in leave_type_candidates:
            if candidate in row.index:
                leave_type_val = row.get(candidate, '')
                leave_type = str(leave_type_val).strip() if pd.notna(leave_type_val) else '请假'
                break

        # 只有当请假时长大于0时才创建记录
        if leave_hours > 0:
            record = WorkHourData(
                serial_no=serial_no,
                user_name=user_name,
                start_time=start_time,
                end_time=end_time,
                work_type='leave',
                project_name=leave_type if leave_type else '请假',
                project_manager='',
                work_hours=0.0,
                overtime_hours=0.0,
                leave_hours=leave_hours,
                work_content=leave_type if leave_type else '请假',
                approval_result=approval_result,
                approval_status=approval_status,
                dept_name=dept_name,
                import_batch_no=batch_no
            )
            records.append(record)
            created_count += 1

    return records, created_count


@import_bp.route('/import/upload', methods=['POST'])
@auth_required
def upload_file():
    """上传Excel文件并导入数据"""
    try:
        # 检查文件
        if 'file' not in request.files:
            return error_response(2001, '未上传文件', http_status=400)

        file = request.files['file']
        if file.filename == '':
            return error_response(2001, '未选择文件', http_status=400)

        if not allowed_file(file.filename):
            return error_response(2002, '文件格式错误，仅支持.xlsx或.xls格式', http_status=400)

        # 获取参数
        duplicate_strategy = request.form.get('duplicateStrategy', 'skip')

        # 保存临时文件（保留原始文件名用于显示）
        original_filename = file.filename  # 原始文件名，用于显示
        safe_filename = secure_filename(file.filename)  # 安全文件名，用于存储
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        stored_filename = f"{timestamp}_{safe_filename}"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_filename)
        file.save(upload_path)

        # 验证文件
        is_valid, error_msg = validate_excel_file(upload_path)
        if not is_valid:
            os.remove(upload_path)
            return error_response(2003, error_msg, http_status=400)

        # 读取数据
        df = read_excel_data(upload_path)
        if df is None:
            os.remove(upload_path)
            return error_response(2003, 'Excel文件解析失败', http_status=400)

        # 生成批次号
        batch_no = generate_batch_no('IMP')

        # 初始化统计
        total_rows = len(df)
        success_rows = 0
        repeat_rows = 0
        invalid_rows = 0
        errors = []
        repeats = []  # 存储重复数据详情

        # 获取系统配置
        config = SysConfig.query.filter_by(config_key='import.max_rows').first()
        max_rows = int(config.config_value) if config else 1000

        if total_rows > max_rows:
            os.remove(upload_path)
            return error_response(2004, f'单次导入不能超过{max_rows}行', http_status=400)

        # 处理每一行数据
        # 调整必填字段：基础信息必须填写，工时类型至少要有一种
        required_fields = ['序号', '姓名', '开始时间', '结束时间', '审批结果', '审批状态']

        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel行号(含表头)

            # 验证必填字段
            is_valid, error_list = validate_work_hour_row(row, required_fields)
            if not is_valid:
                invalid_rows += 1
                # 为每个错误添加行号
                for error_item in error_list:
                    errors.append({
                        'row': row_num,
                        'field': error_item['field'],
                        'error': error_item['error']
                    })
                continue

            # 提取基础数据
            serial_no = str(row['序号']).strip()
            user_name = str(row['姓名']).strip()
            start_time_str = str(row['开始时间']).strip()
            end_time_str = str(row['结束时间']).strip()
            approval_result = str(row['审批结果']).strip()
            approval_status = str(row['审批状态']).strip()

            # 解析时间（只取日期部分）
            try:
                start_time_dt = pd.to_datetime(start_time_str)
                end_time_dt = pd.to_datetime(end_time_str)
                # 只保留日期部分，去掉时间
                start_time = start_time_dt.date()
                end_time = end_time_dt.date()
            except:
                invalid_rows += 1
                errors.append({
                    'row': row_num,
                    'field': '开始时间',
                    'error': '时间格式错误'
                })
                continue

            # 拆分数据为多条记录（按工时类型）
            records, created_count = split_work_types(
                row, serial_no, user_name, start_time, end_time,
                batch_no, approval_result, approval_status
            )

            # 验证至少有一种工时类型
            if created_count == 0:
                invalid_rows += 1
                errors.append({
                    'row': row_num,
                    'field': '工时数据',
                    'error': '至少需要一种工时类型的数据（项目交付/产研项目/售前支持/部门内务/请假）'
                })
                continue

            # 检查唯一性和添加记录
            for record in records:
                # 检查唯一性：同一人同一时间同一项目同一类型（历史批次）
                existing = WorkHourData.query.filter(
                    WorkHourData.user_name == record.user_name,
                    WorkHourData.start_time == record.start_time,
                    WorkHourData.project_name == record.project_name,
                    WorkHourData.work_type == record.work_type,
                    WorkHourData.import_batch_no != batch_no  # 排除当前批次
                ).first()

                if existing:
                    # 记录重复数据详情
                    repeats.append({
                        'row': row_num,
                        'field': '数据重复',
                        'error': f'姓名{user_name}、时间{start_time_str}、项目{record.project_name}、类型{record.work_type}的数据已存在',
                        'existing_batch': existing.import_batch_no
                    })

                    if duplicate_strategy == 'cover':
                        # 更新现有记录
                        existing.end_time = record.end_time
                        existing.approval_result = record.approval_result
                        existing.approval_status = record.approval_status
                        existing.work_hours = record.work_hours
                        existing.overtime_hours = record.overtime_hours
                        existing.leave_hours = record.leave_hours
                        existing.project_manager = record.project_manager
                        existing.work_content = record.work_content
                        existing.dept_name = record.dept_name
                        existing.import_batch_no = batch_no
                        existing.updated_at = datetime.now()
                        repeat_rows += 1
                    else:
                        # 跳过
                        repeat_rows += 1
                else:
                    # 添加新记录
                    db.session.add(record)
                    success_rows += 1

        # 创建导入记录
        import_record = ImportRecord(
            batch_no=batch_no,
            file_name=original_filename,  # 使用原始文件名
            total_rows=total_rows,
            success_rows=success_rows,
            repeat_rows=repeat_rows,
            invalid_rows=invalid_rows,
            duplicate_strategy=duplicate_strategy,
            import_user=request.current_user.get('userName'),  # 从JWT获取当前用户
            file_size=os.path.getsize(upload_path)
        )

        if errors:
            import json
            import_record.error_details = json.dumps(errors, ensure_ascii=False)  # 保存为JSON格式

        if repeats:
            import json
            import_record.repeat_details = json.dumps(repeats, ensure_ascii=False)  # 保存为JSON格式

        db.session.add(import_record)
        db.session.commit()

        # 删除临时文件
        os.remove(upload_path)

        return success_response(data={
            'batchNo': batch_no,
            'totalRows': total_rows,
            'successRows': success_rows,
            'repeatRows': repeat_rows,
            'invalidRows': invalid_rows,
            'errors': errors  # 返回所有错误
        }, message='导入完成')

    except Exception as e:
        db.session.rollback()
        return error_response(500, f'导入失败: {str(e)}', http_status=500)


@import_bp.route('/import/records', methods=['GET'])
@auth_required
def get_import_records():
    """获取导入记录列表"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        file_name = request.args.get('fileName', '')
        start_date = request.args.get('startDate', '')
        end_date = request.args.get('endDate', '')

        # 构建查询
        query = ImportRecord.query

        # 文件名模糊搜索
        if file_name:
            query = query.filter(ImportRecord.file_name.like(f'%{file_name}%'))

        # 时间范围过滤
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(ImportRecord.import_time >= start_datetime)

        if end_date:
            # 结束日期包含当天，需要加一天
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            from datetime import timedelta
            end_datetime = end_datetime + timedelta(days=1)
            query = query.filter(ImportRecord.import_time < end_datetime)

        pagination = query.order_by(
            ImportRecord.import_time.desc()
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
        return error_response(500, str(e), http_status=500)


@import_bp.route('/import/record/<batch_no>', methods=['GET'])
@auth_required
def get_import_detail(batch_no):
    """获取导入记录详情"""
    try:
        record = ImportRecord.query.filter_by(batch_no=batch_no).first()

        if not record:
            return error_response(3001, '导入记录不存在', http_status=404)

        data = record.to_dict()

        # 解析错误详情
        if record.error_details:
            try:
                import json
                data['errors'] = json.loads(record.error_details)
            except:
                # 兼容旧格式（Python字符串格式）
                try:
                    import ast
                    data['errors'] = ast.literal_eval(record.error_details)
                except:
                    data['errors'] = []
        else:
            data['errors'] = []

        # 解析重复数据详情
        if record.repeat_details:
            try:
                import json
                data['repeats'] = json.loads(record.repeat_details)
            except:
                # 兼容旧格式（Python字符串格式）
                try:
                    import ast
                    data['repeats'] = ast.literal_eval(record.repeat_details)
                except:
                    data['repeats'] = []
        else:
            data['repeats'] = []

        # 添加摘要信息
        data['summary'] = {
            'successRate': f"{(record.success_rows / record.total_rows * 100):.1f}%" if record.total_rows > 0 else "0%",
            'repeatRate': f"{(record.repeat_rows / record.total_rows * 100):.1f}%" if record.total_rows > 0 else "0%",
            'invalidRate': f"{(record.invalid_rows / record.total_rows * 100):.1f}%" if record.total_rows > 0 else "0%"
        }

        return success_response(data=data)

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@import_bp.route('/import/record/<batch_no>/data', methods=['GET'])
@auth_required
def get_import_data_view(batch_no):
    """查看导入批次的数据"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))

        record = ImportRecord.query.filter_by(batch_no=batch_no).first()
        if not record:
            return error_response(3001, '导入记录不存在', http_status=404)

        pagination = WorkHourData.query.filter_by(
            import_batch_no=batch_no
        ).order_by(WorkHourData.id.asc()).paginate(
            page=page, per_page=size, error_out=False
        )

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
