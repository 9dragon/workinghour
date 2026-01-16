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
        required_fields = ['序号', '姓名', '开始时间', '结束时间', '项目交付-项目名称',
                          '审批结果', '审批状态', '项目交付-工作时长']

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

            # 提取数据
            serial_no = str(row['序号']).strip()
            user_name = str(row['姓名']).strip()
            start_time_str = str(row['开始时间']).strip()
            end_time_str = str(row['结束时间']).strip()
            project_name = str(row['项目交付-项目名称']).strip()

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

            # 检查唯一性：同一人同一时间同一项目，排除当前批次的数据
            existing = WorkHourData.query.filter(
                WorkHourData.user_name == user_name,
                WorkHourData.start_time == start_time,
                WorkHourData.project_name == project_name,
                WorkHourData.import_batch_no != batch_no  # 排除当前批次
            ).first()

            if existing:
                # 记录重复数据详情
                repeats.append({
                    'row': row_num,
                    'field': '数据重复',
                    'error': f'姓名{user_name}、时间{start_time_str}、项目{project_name}的数据已存在',
                    'existing_batch': existing.import_batch_no
                })

                if duplicate_strategy == 'cover':
                    # 更新现有记录
                    existing.end_time = end_time
                    existing.approval_result = str(row['审批结果']).strip()
                    existing.approval_status = str(row['审批状态']).strip()

                    # 处理工作时长：NaN转换为0
                    work_val = row.get('项目交付-工作时长', 0)
                    existing.work_hours = 0.0 if (pd.isna(work_val) or work_val == '') else float(work_val)

                    # 处理加班时长：NaN转换为0
                    overtime_val = row.get('项目交付-加班时长', 0)
                    existing.overtime_hours = 0.0 if (pd.isna(overtime_val) or overtime_val == '') else float(overtime_val)

                    existing.project_manager = str(row.get('项目交付-项目经理', '')).strip() if pd.notna(row.get('项目交付-项目经理')) else ''
                    existing.work_content = str(row.get('项目交付-工作内容', '')).strip() if pd.notna(row.get('项目交付-工作内容')) else ''
                    existing.dept_name = str(row.get('部门', '')).strip() if pd.notna(row.get('部门')) else ''
                    existing.import_batch_no = batch_no
                    existing.updated_at = datetime.now()
                    repeat_rows += 1
                else:
                    # 跳过
                    repeat_rows += 1
                continue

            # 创建新记录
            # 处理加班时长：NaN转换为0
            overtime_val = row.get('项目交付-加班时长', 0)
            if pd.isna(overtime_val) or overtime_val == '':
                overtime_hours = 0.0
            else:
                overtime_hours = float(overtime_val)

            # 处理工作时长：NaN转换为0
            work_val = row.get('项目交付-工作时长', 0)
            if pd.isna(work_val) or work_val == '':
                work_hours = 0.0
            else:
                work_hours = float(work_val)

            work_hour = WorkHourData(
                serial_no=serial_no,
                user_name=user_name,
                start_time=start_time,
                end_time=end_time,
                project_name=project_name,
                approval_result=str(row['审批结果']).strip(),
                approval_status=str(row['审批状态']).strip(),
                work_hours=work_hours,
                overtime_hours=overtime_hours,
                project_manager=str(row.get('项目交付-项目经理', '')).strip() if pd.notna(row.get('项目交付-项目经理')) else '',
                work_content=str(row.get('项目交付-工作内容', '')).strip() if pd.notna(row.get('项目交付-工作内容')) else '',
                dept_name=str(row.get('部门', '')).strip() if pd.notna(row.get('部门')) else '',
                import_batch_no=batch_no
            )

            db.session.add(work_hour)
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
