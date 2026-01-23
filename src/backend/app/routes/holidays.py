"""
节假日管理路由
"""
from flask import Blueprint, request
from app.models.db import db
from app.models.holiday import Holiday
from app.utils.response import success_response, error_response
from datetime import datetime

holidays_bp = Blueprint('holidays', __name__)


@holidays_bp.route('/holidays', methods=['GET'])
def get_holidays():
    """获取节假日列表"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        year = request.args.get('year', type=int)
        is_workday = request.args.get('isWorkday', type=bool)

        query = Holiday.query

        if year:
            query = query.filter_by(year=year)

        if is_workday is not None:
            query = query.filter_by(is_workday=is_workday)

        pagination = query.order_by(
            Holiday.holiday_date.asc()
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


@holidays_bp.route('/holidays', methods=['POST'])
def add_holiday():
    """添加节假日"""
    try:
        data = request.get_json()
        holiday_date_str = data.get('holidayDate')
        holiday_name = data.get('holidayName', '').strip()
        is_workday = data.get('isWorkday', False)
        data_source = data.get('dataSource', 'manual')
        created_by = data.get('createdBy', 'system')

        if not holiday_date_str:
            return error_response(4001, '节假日日期不能为空'), 400

        if not holiday_name:
            return error_response(4002, '节假日名称不能为空'), 400

        try:
            holiday_date = datetime.strptime(holiday_date_str, '%Y-%m-%d').date()
        except ValueError:
            return error_response(4003, '日期格式错误，应为YYYY-MM-DD'), 400

        # 检查是否已存在
        existing = Holiday.query.filter_by(holiday_date=holiday_date).first()
        if existing:
            return error_response(4004, '该日期已存在'), 400

        year = holiday_date.year

        holiday = Holiday(
            holiday_date=holiday_date,
            holiday_name=holiday_name,
            is_workday=is_workday,
            data_source=data_source,
            year=year,
            created_by=created_by
        )

        db.session.add(holiday)
        db.session.commit()

        return success_response(data=holiday.to_dict(), message='添加成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@holidays_bp.route('/holidays/<int:holiday_id>', methods=['DELETE'])
def delete_holiday(holiday_id):
    """删除节假日"""
    try:
        holiday = Holiday.query.get(holiday_id)

        if not holiday:
            return error_response(3001, '节假日记录不存在'), 404

        db.session.delete(holiday)
        db.session.commit()

        return success_response(message='删除成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e)), 500


@holidays_bp.route('/holidays/batch', methods=['POST'])
def batch_import_holidays():
    """批量导入节假日"""
    try:
        data = request.get_json()
        holidays_list = data.get('holidays', [])
        created_by = data.get('createdBy', 'system')

        if not holidays_list:
            return error_response(4001, '节假日列表不能为空'), 400

        success_count = 0
        skip_count = 0
        skipped = []

        for holiday_data in holidays_list:
            holiday_date_str = holiday_data.get('holidayDate')
            holiday_name = holiday_data.get('holidayName', '').strip()
            is_workday = holiday_data.get('isWorkday', False)
            data_source = holiday_data.get('dataSource', 'manual')

            if not holiday_date_str or not holiday_name:
                continue

            try:
                holiday_date = datetime.strptime(holiday_date_str, '%Y-%m-%d').date()
            except ValueError:
                skipped.append(holiday_date_str)
                continue

            # 检查是否已存在
            existing = Holiday.query.filter_by(holiday_date=holiday_date).first()
            if existing:
                skip_count += 1
                skipped.append(holiday_date_str)
                continue

            year = holiday_date.year

            holiday = Holiday(
                holiday_date=holiday_date,
                holiday_name=holiday_name,
                is_workday=is_workday,
                data_source=data_source,
                year=year,
                created_by=created_by
            )

            db.session.add(holiday)
            success_count += 1

        db.session.commit()

        return success_response(data={
            'total': len(holidays_list),
            'successCount': success_count,
            'skipCount': skip_count,
            'skipped': skipped
        }, message='批量导入完成')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)
