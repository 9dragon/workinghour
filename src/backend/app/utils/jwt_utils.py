"""
JWT工具函数
"""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import os

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 8

def generate_token(user_info):
    """生成JWT令牌"""
    payload = {
        'userName': user_info.get('userName'),
        'realName': user_info.get('realName'),
        'role': user_info.get('role', 'user'),
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def decode_token(token):
    """解码JWT令牌"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, '令牌已过期'
    except jwt.InvalidTokenError:
        return None, '令牌无效'

def auth_required(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({
                'code': 9002,
                'message': '未认证或令牌过期',
                'error': 'Missing authorization header'
            }), 401

        if not token.startswith('Bearer '):
            return jsonify({
                'code': 9002,
                'message': '未认证或令牌过期',
                'error': 'Invalid authorization header format'
            }), 401

        token = token.split(' ')[1]
        payload, error = decode_token(token)

        if error:
            return jsonify({
                'code': 9002,
                'message': '未认证或令牌过期',
                'error': error
            }), 401

        # 将用户信息附加到请求对象
        request.current_user = payload

        return f(*args, **kwargs)

    return decorated_function
