"""
统一响应格式工具
"""
from flask import jsonify
from datetime import datetime

def success_response(data=None, message="操作成功"):
    """成功响应"""
    response = {
        'code': 200,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(response)

def error_response(code, message, error=None, http_status=None):
    """错误响应"""
    response = {
        'code': code,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    if error:
        response['error'] = error
    status_code = http_status if http_status else (code if code >= 400 else 200)
    return jsonify(response), status_code

def paginated_response(list_data, total, page, size):
    """分页响应"""
    total_pages = (total + size - 1) // size
    data = {
        'list': list_data,
        'total': total,
        'page': page,
        'size': size,
        'totalPages': total_pages
    }
    return success_response(data=data)
