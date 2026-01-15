"""
用户认证路由
"""
from flask import Blueprint, request
from app.models.db import db
from app.models.user import User
from app.utils.jwt_utils import generate_token, auth_required
from app.utils.response import success_response, error_response
from datetime import datetime
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        # 参数验证
        if not username:
            return error_response(1001, '用户名不能为空', http_status=401)
        if not password:
            return error_response(1002, '密码不能为空', http_status=401)
        if len(password) < 6:
            return error_response(1002, '密码长度不能少于6位', http_status=401)

        # 查找用户
        user = User.query.filter_by(user_name=username).first()

        if not user:
            return error_response(1003, '用户名或密码错误', http_status=401)

        # 检查账号锁定状态
        if user.is_locked():
            remaining_time = user.get_lock_remaining_time()
            return error_response(1004, f'账号已锁定，请{remaining_time}分钟后再试', http_status=401)

        # 验证密码
        if not user.check_password(password):
            # 增加失败次数
            user.login_fail_count += 1
            if user.login_fail_count >= 5:
                user.lock_time = datetime.now()
                db.session.commit()
                return error_response(1004, '密码错误次数过多，账号已锁定30分钟', http_status=401)
            db.session.commit()
            return error_response(1003, '用户名或密码错误', http_status=401)

        # 登录成功，重置失败次数
        user.login_fail_count = 0
        user.lock_time = None
        user.last_login_time = datetime.now()
        db.session.commit()

        # 生成令牌
        user_info = {
            'userName': user.user_name,
            'realName': user.real_name,
            'role': user.role
        }
        token = generate_token(user_info)

        return success_response(data={
            'token': token,
            'tokenType': 'Bearer',
            'expiresIn': 8 * 3600,  # 8小时
            'userInfo': user_info
        }, message='登录成功')

    except Exception as e:
        return error_response(500, f'登录失败: {str(e)}', http_status=500)

@auth_bp.route('/logout', methods=['POST'])
@auth_required
def logout():
    """用户登出"""
    # JWT无状态，客户端删除token即可
    return success_response(message='登出成功')

@auth_bp.route('/user/info', methods=['GET'])
@auth_required
def get_user_info():
    """获取当前用户信息"""
    try:
        user_info = request.current_user
        return success_response(data={
            'userName': user_info.get('userName'),
            'realName': user_info.get('realName'),
            'role': user_info.get('role')
        })
    except Exception as e:
        return error_response(500, str(e), http_status=500)
