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

        # 保存临时文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)
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

        # 获取系统配置
        max_rows = int(db.session.query(db.func.json_extract(
            db.cast(SysConfig.config_value, db.String), '$'
        )).filter_by(config_key='import.max_rows').first() or [1000])[0]

        if total_rows > max_rows:
            os.remove(upload_path)
            return error_response(2004, f'单次导入不能超过{max_rows}行', http_status=400)

        # 处理每一行数据
        required_fields = ['序号', '姓名', '开始时间', '结束时间', '项目名称',
                          '审批结果', '审批状态', '项目交付-工作时长']

        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel行号(含表头)

            # 验证必填字段
            is_valid, error_msg = validate_work_hour_row(row, required_fields)
            if not is_valid:
                invalid_rows += 1
                errors.append({
                    'row': row_num,
                    'field': 'multiple',
                    'error': error_msg
                })
                continue

            # 提取数据
            serial_no = str(row['序号']).strip()
            user_name = str(row['姓名']).strip()
            start_time_str = str(row['开始时间']).strip()
            end_time_str = str(row['结束时间']).strip()
            project_name = str(row['项目名称']).strip()

            # 解析时间
            try:
                start_time = pd.to_datetime(start_time_str)
                end_time = pd.to_datetime(end_time_str)
            except:
                invalid_rows += 1
                errors.append({
                    'row': row_num,
                    'field': 'start_time',
                    'error': '时间格式错误'
                })
                continue

            # 检查唯一性
            existing = WorkHourData.query.filter_by(
                serial_no=serial_no,
                user_name=user_name,
                start_time=start_time,
                project_name=project_name
            ).first()

            if existing:
                if duplicate_strategy == 'cover':
                    # 更新现有记录
                    existing.end_time = end_time
                    existing.approval_result = str(row['审批结果']).strip()
                    existing.approval_status = str(row['审批状态']).strip()
                    existing.work_hours = float(row.get('项目交付-工作时长', 0))
                    existing.overtime_hours = float(row.get('项目交付-加班时长', 0))
                    existing.project_manager = str(row.get('项目经理', '')).strip()
                    existing.dept_name = str(row.get('部门', '')).strip()
                    existing.work_date = start_time.date()
                    existing.import_batch_no = batch_no
                    existing.updated_at = datetime.now()
                    repeat_rows += 1
                else:
                    # 跳过
                    repeat_rows += 1
                continue

            # 创建新记录
            work_hour = WorkHourData(
                serial_no=serial_no,
                user_name=user_name,
                start_time=start_time,
                end_time=end_time,
                project_name=project_name,
                approval_result=str(row['审批结果']).strip(),
                approval_status=str(row['审批状态']).strip(),
                work_hours=float(row.get('项目交付-工作时长', 0)),
                overtime_hours=float(row.get('项目交付-加班时长', 0)),
                project_manager=str(row.get('项目经理', '')).strip(),
                dept_name=str(row.get('部门', '')).strip(),
                work_date=start_time.date(),
                import_batch_no=batch_no
            )

            db.session.add(work_hour)
            success_rows += 1

        # 创建导入记录
        import_record = ImportRecord(
            batch_no=batch_no,
            file_name=filename,
            total_rows=total_rows,
            success_rows=success_rows,
            repeat_rows=repeat_rows,
            invalid_rows=invalid_rows,
            duplicate_strategy=duplicate_strategy,
            import_user=request.current_user.get('userName') if hasattr(request, 'current_user') else 'system',
            file_size=os.path.getsize(upload_path)
        )

        if errors:
            import_record.error_details = str(errors[:100])  # 保存前100个错误

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
            'errors': errors if len(errors) <= 100 else errors[:100]
        }, message='导入完成')

    except Exception as e:
        db.session.rollback()
        return error_response(500, f'导入失败: {str(e)}', http_status=500)


@import_bp.route('/import/records', methods=['GET'])
def get_import_records():
    """获取导入记录列表"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))

        pagination = ImportRecord.query.order_by(
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
def get_import_detail(batch_no):
    """获取导入记录详情"""
    try:
        record = ImportRecord.query.filter_by(batch_no=batch_no).first()

        if not record:
            return error_response(3001, '导入记录不存在', http_status=404)

        data = record.to_dict()

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
        ).order_by(WorkHourData.start_time.desc()).paginate(
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
