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
        is_weekend = request.args.get('isWeekend', type=bool)
        data_source = request.args.get('dataSource')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')

        query = Holiday.query

        if year:
            query = query.filter_by(year=year)

        if is_workday is not None:
            query = query.filter_by(is_workday=is_workday)

        if is_weekend is not None:
            query = query.filter_by(is_weekend=is_weekend)

        if data_source:
            query = query.filter_by(data_source=data_source)

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Holiday.holiday_date >= start)

        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Holiday.holiday_date <= end)

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


@holidays_bp.route('/holidays/sync/<int:year>', methods=['POST'])
def sync_holidays(year):
    """从第三方API同步节假日数据（timor.tech）"""
    try:
        import requests

        # 获取请求参数
        request_data = request.get_json() or {}
        mode = request_data.get('mode', 'skip')  # skip 或 overwrite

        # 调用 timor.tech 免费节假日API
        api_url = f"https://timor.tech/api/holiday/year/{year}"

        # 添加请求头避免403错误
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get('code') != 0:
            return error_response(5001, f'第三方API返回错误: {data.get("message", "未知错误")}', http_status=500)

        holidays = data.get('holiday', [])
        if not holidays:
            return error_response(5002, '第三方API未返回节假日数据', http_status=500)

        success_count = 0
        skip_count = 0

        # 遍历返回的节假日数据
        for date_str, holiday_info in holidays.items():
            try:
                # timor.tech返回的key是 "MM-DD" 格式，需要拼接年份
                full_date_str = f"{year}-{date_str}"
                holiday_date = datetime.strptime(full_date_str, '%Y-%m-%d').date()

                # timor.tech返回格式：holiday为true表示节假日，false表示调休工作日
                if not isinstance(holiday_info, dict):
                    continue

                is_holiday = holiday_info.get('holiday', False)
                if not is_holiday:
                    # 如果是调休工作日，标记为调休
                    is_workday = True
                    holiday_name = holiday_info.get('name', '调休')
                else:
                    is_workday = False
                    holiday_name = holiday_info.get('name', '节假日')

                # 检查是否已存在数据
                existing = Holiday.query.filter_by(holiday_date=holiday_date).first()

                if existing:
                    if mode == 'overwrite':
                        # 覆盖模式：仅覆盖API来源的数据
                        if existing.data_source == 'api':
                            db.session.delete(existing)
                        elif existing.data_source == 'manual':
                            # 手动数据不被覆盖
                            skip_count += 1
                            continue
                        elif existing.data_source == 'auto':
                            # 自动生成的周末数据也不覆盖
                            skip_count += 1
                            continue
                    else:
                        # 跳过模式：跳过所有已存在的数据
                        skip_count += 1
                        continue

                # 添加新的节假日/调休记录
                holiday = Holiday(
                    holiday_date=holiday_date,
                    holiday_name=holiday_name,
                    is_workday=is_workday,
                    data_source='api',
                    year=year,
                    created_by='system'
                )

                db.session.add(holiday)
                success_count += 1

            except Exception:
                # 跳过处理失败的记录，继续处理下一条
                continue

        db.session.commit()

        return success_response(data={
            'year': year,
            'total': len(holidays),
            'successCount': success_count,
            'skipCount': skip_count,
            'dataSource': 'api'
        }, message=f'成功同步{year}年节假日')

    except requests.exceptions.RequestException as e:
        return error_response(5003, f'请求第三方API失败: {str(e)}', http_status=500)
    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@holidays_bp.route('/holidays/generate-weekends/<int:year>', methods=['POST'])
def generate_weekends(year):
    """生成指定年份的周末数据"""
    try:
        from datetime import date, timedelta

        # 获取请求参数
        request_data = request.get_json() or {}
        mode = request_data.get('mode', 'skip')  # skip 或 overwrite

        # 生成该年份的所有日期
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        current_date = start_date
        generated_count = 0
        skip_count = 0

        while current_date <= end_date:
            # 判断是否为周末（周六=5，周日=6）
            is_weekend = current_date.weekday() >= 5

            if is_weekend:
                # 检查是否已存在
                existing = Holiday.query.filter_by(holiday_date=current_date).first()

                if existing:
                    if mode == 'overwrite':
                        # 覆盖模式：仅覆盖auto来源的数据
                        if existing.data_source == 'auto':
                            db.session.delete(existing)
                        else:
                            # 其他来源的数据不被覆盖
                            skip_count += 1
                            current_date += timedelta(days=1)
                            continue
                    else:
                        # 跳过模式：跳过已存在的数据
                        skip_count += 1
                        current_date += timedelta(days=1)
                        continue

                # 添加周末记录
                weekend = Holiday(
                    holiday_date=current_date,
                    holiday_name='周末',
                    is_workday=False,
                    is_weekend=True,
                    data_source='auto',
                    year=year,
                    created_by='system'
                )

                db.session.add(weekend)
                generated_count += 1

            current_date += timedelta(days=1)

        db.session.commit()

        return success_response(data={
            'year': year,
            'total': 104,
            'generatedCount': generated_count,
            'skipCount': skip_count,
            'dataSource': 'auto'
        }, message=f'成功生成{year}年周末数据')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@holidays_bp.route('/holidays/clear-all', methods=['DELETE'])
def clear_all_holidays():
    """清空所有节假日数据"""
    try:
        # 统计当前数据
        total_count = Holiday.query.count()

        if total_count == 0:
            return success_response(message='数据库中无节假日数据', data={
                'deletedCount': 0
            })

        # 删除所有记录
        Holiday.query.delete()
        db.session.commit()

        return success_response(data={
            'deletedCount': total_count
        }, message=f'已清空 {total_count} 条节假日数据')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e)), 500


@holidays_bp.route('/holidays/summary', methods=['GET'])
def get_holiday_summary():
    """获取节假日统计数据"""
    try:
        year = request.args.get('year', type=int)

        query = Holiday.query

        if year:
            query = query.filter_by(year=year)

        # 统计总数
        total = query.count()

        # 统计法定节假日（非周末、非调休）
        legal = query.filter_by(is_workday=False, is_weekend=False).count()

        # 统计调休工作日
        workdays = query.filter_by(is_workday=True).count()

        # 统计周末
        weekends = query.filter_by(is_weekend=True).count()

        # 按数据来源统计
        manual = query.filter_by(data_source='manual').count()
        api = query.filter_by(data_source='api').count()
        auto = query.filter_by(data_source='auto').count()

        return success_response(data={
            'total': total,
            'legal': legal,
            'workdays': workdays,
            'weekends': weekends,
            'manual': manual,
            'api': api,
            'auto': auto
        })

    except Exception as e:
        return error_response(500, str(e)), 500
