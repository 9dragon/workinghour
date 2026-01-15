"""
工具函数
"""
import os
import json
from datetime import datetime, timedelta
import pandas as pd
from openpyxl import load_workbook

def generate_batch_no(prefix='IMP'):
    """生成批次号"""
    now = datetime.now()
    timestamp = now.strftime('%Y%m%d%H%M%S')
    import random
    random_num = random.randint(1000, 9999)
    return f'{prefix}_{timestamp}_{random_num}'

def validate_excel_file(file_path):
    """
    验证Excel文件

    返回: (is_valid, error_message)
    """
    try:
        # 检查文件扩展名
        if not file_path.endswith(('.xls', '.xlsx')):
            return False, '文件格式错误，仅支持.xlsx或.xls格式'

        # 检查文件大小（10MB限制）
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:
            return False, '文件大小超过10MB限制'

        # 尝试读取文件
        wb = load_workbook(file_path, read_only=True, data_only=True)
        ws = wb.active

        # 检查是否有数据
        if ws.max_row < 2:
            return False, 'Excel文件没有数据'

        return True, None

    except Exception as e:
        return False, f'文件解析失败: {str(e)}'

def read_excel_data(file_path):
    """
    读取Excel数据

    返回: DataFrame or None
    """
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        print(f"读取Excel失败: {str(e)}")
        return None

def validate_work_hour_row(row, required_fields):
    """
    验证工时数据行

    返回: (is_valid, error_message)
    """
    errors = []

    # 检查必填字段
    for field in required_fields:
        if pd.isna(row.get(field, '')) or str(row.get(field, '')).strip() == '':
            errors.append(f"{field}字段为空")

    # 检查审批结果和状态
    approval_result = str(row.get('审批结果', '')).strip()
    approval_status = str(row.get('审批状态', '')).strip()

    if approval_result != '通过':
        errors.append(f"审批结果为'{approval_result}'，仅支持'通过'")

    if approval_status != '已完成':
        errors.append(f"审批状态为'{approval_status}'，仅支持'已完成'")

    # 检查工作时长
    try:
        work_hours = float(row.get('项目交付-工作时长', 0))
        if work_hours < 0:
            errors.append("工作时长不能为负数")
        if work_hours > 24:
            errors.append("工作时长超过24小时")
    except:
        errors.append("工作时长格式错误")

    # 检查加班时长
    try:
        overtime_hours = float(row.get('项目交付-加班时长', 0))
        if overtime_hours < 0:
            errors.append("加班时长不能为负数")
    except:
        errors.append("加班时长格式错误")

    if errors:
        return False, '; '.join(errors)
    return True, None

def calculate_date_range(start_date, end_date, max_days=90):
    """
    计算日期范围，验证不超过max_days天

    返回: (is_valid, error_message, days_count)
    """
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        if start > end:
            return False, "开始日期不能晚于结束日期", 0

        days_count = (end - start).days
        if days_count > max_days:
            return False, f"时间范围不能超过{max_days}天", days_count

        return True, None, days_count
    except ValueError as e:
        return False, "日期格式错误，应为YYYY-MM-DD", 0

def get_workdays_in_range(start_date, end_date, workdays):
    """
    获取指定时间范围内的工作日列表

    参数:
        start_date: 开始日期 (datetime.date)
        end_date: 结束日期 (datetime.date)
        workdays: 工作日列表 [1,2,3,4,5] (1=周一, 7=周日)

    返回: 工作日日期列表
    """
    workdays_list = []
    current = start_date

    while current <= end_date:
        if current.weekday() + 1 in workdays:  # weekday()+1转换为1-7
            workdays_list.append(current)
        current += timedelta(days=1)

    return workdays_list
