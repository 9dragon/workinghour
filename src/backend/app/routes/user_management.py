"""
用户管理路由
"""
from flask import Blueprint, request
from app.models.db import db
from app.models.user import User
from app.utils.response import success_response, error_response
from app.utils.jwt_utils import auth_required

user_mgmt_bp = Blueprint('user_management', __name__)


@user_mgmt_bp.route('/users', methods=['GET'])
@auth_required
def get_users():
    """获取用户列表"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        keyword = request.args.get('keyword', '')

        query = User.query
        if keyword:
            query = query.filter(
                db.or_(
                    User.user_name.like(f'%{keyword}%'),
                    User.email.like(f'%{keyword}%')
                )
            )

        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        users = [user.to_dict() for user in pagination.items]

        return success_response(data={
            'list': users,
            'total': pagination.total,
            'page': page,
            'size': size
        })

    except Exception as e:
        return error_response(500, str(e), http_status=500)


@user_mgmt_bp.route('/users', methods=['POST'])
@auth_required
def create_user():
    """创建用户"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('userName'):
            return error_response(7001, '用户名不能为空', http_status=400)

        if not data.get('password'):
            return error_response(7002, '密码不能为空', http_status=400)

        # 检查用户是否已存在
        existing_user = User.query.filter_by(user_name=data['userName']).first()
        if existing_user:
            return error_response(7003, '该用户名已存在', http_status=400)

        # 创建用户
        user = User(
            user_name=data['userName'],
            email=data.get('email', ''),
            role=data.get('role', 'user')
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        return success_response(data=user.to_dict(), message='创建成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@user_mgmt_bp.route('/users/<int:user_id>', methods=['PUT'])
@auth_required
def update_user(user_id):
    """更新用户信息"""
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response(7004, '用户不存在', http_status=404)

        data = request.get_json()

        if 'email' in data:
            user.email = data['email']
        if 'role' in data:
            user.role = data['role']
        if 'status' in data:
            user.status = data['status']

        db.session.commit()

        return success_response(data=user.to_dict(), message='更新成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@user_mgmt_bp.route('/users/<int:user_id>', methods=['DELETE'])
@auth_required
def delete_user(user_id):
    """删除用户"""
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response(7005, '用户不存在', http_status=404)

        # 不允许删除管理员
        if user.role == 'admin':
            return error_response(7006, '不能删除管理员用户', http_status=400)

        db.session.delete(user)
        db.session.commit()

        return success_response(message='删除成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@user_mgmt_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@auth_required
def reset_user_password(user_id):
    """重置用户密码"""
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response(7007, '用户不存在', http_status=404)

        data = request.get_json()
        new_password = data.get('password', '123456')

        user.set_password(new_password)
        user.login_fail_count = 0  # 重置登录失败次数
        user.lock_time = None  # 解除锁定

        db.session.commit()

        return success_response(message='密码重置成功')

    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)

