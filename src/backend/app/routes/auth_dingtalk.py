"""
钉钉免登录路由
"""
from flask import Blueprint, request, current_app
from app.models.db import db
from app.models.user import User
from app.utils.jwt_utils import generate_token
from app.utils.response import success_response, error_response
import requests
import logging

auth_dingtalk_bp = Blueprint('auth_dingtalk', __name__)
logger = logging.getLogger(__name__)

# 钉钉API配置
DINGTALK_GET_USER_INFO_URL = "https://oapi.dingtalk.com/topapi/v2/user/getuserinfo"
DINGTALK_GET_USER_DETAIL_URL = "https://oapi.dingtalk.com/topapi/v2/user/get"


def get_dingtalk_access_token(app_key, app_secret):
    """获取钉钉access_token"""
    url = "https://oapi.dingtalk.com/gettoken"
    params = {
        'appkey': app_key,
        'appsecret': app_secret
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        result = response.json()

        if result.get('errcode') == 0:
            return result.get('access_token')
        else:
            logger.error(f"获取钉钉access_token失败: {result}")
            return None
    except Exception as e:
        logger.error(f"请求钉钉API异常: {e}")
        return None


def get_dingtalk_user_info(access_token, auth_code):
    """通过免登授权码获取用户userId"""
    params = {
        'access_token': access_token
    }
    data = {
        'code': auth_code
    }
    try:
        response = requests.post(
            DINGTALK_GET_USER_INFO_URL,
            params=params,
            json=data,
            timeout=5
        )
        result = response.json()

        if result.get('errcode') == 0:
            return result.get('result')
        else:
            logger.error(f"获取钉钉用户信息失败: {result}")
            return None
    except Exception as e:
        logger.error(f"请求钉钉用户信息API异常: {e}")
        return None


def get_dingtalk_user_detail(access_token, user_id):
    """获取用户详细信息"""
    params = {
        'access_token': access_token
    }
    data = {
        'userid': user_id,
        'language': 'zh_CN'
    }
    try:
        response = requests.post(
            DINGTALK_GET_USER_DETAIL_URL,
            params=params,
            json=data,
            timeout=5
        )
        result = response.json()

        if result.get('errcode') == 0:
            return result.get('result')
        else:
            logger.error(f"获取钉钉用户详情失败: {result}")
            return None
    except Exception as e:
        logger.error(f"请求钉钉用户详情API异常: {e}")
        return None


@auth_dingtalk_bp.route('/dingtalk/login', methods=['POST'])
def dingtalk_login():
    """
    钉钉免登录接口
    前端通过钉钉JSAPI获取authCode，发送到后端验证
    """
    try:
        data = request.get_json()
        auth_code = data.get('authCode')

        if not auth_code:
            return error_response(2001, '免登授权码不能为空', http_status=400)

        # 从配置中获取钉钉应用凭证
        app_key = current_app.config.get('DINGTALK_APP_KEY')
        app_secret = current_app.config.get('DINGTALK_APP_SECRET')

        if not app_key or not app_secret:
            return error_response(2002, '钉钉应用未配置', http_status=500)

        # 1. 获取钉钉access_token
        access_token = get_dingtalk_access_token(app_key, app_secret)
        if not access_token:
            return error_response(2003, '获取钉钉凭证失败', http_status=500)

        # 2. 通过authCode获取用户userId
        user_info = get_dingtalk_user_info(access_token, auth_code)
        if not user_info:
            return error_response(2004, '获取钉钉用户信息失败', http_status=401)

        user_id = user_info.get('userid')

        # 3. 获取用户详细信息
        user_detail = get_dingtalk_user_detail(access_token, user_id)
        if not user_detail:
            # 如果获取详情失败，使用基础信息
            username = user_id
            real_name = user_id
        else:
            username = user_id  # 使用钉钉userId作为用户名
            real_name = user_detail.get('name', user_id)
            email = user_detail.get('email', '')
            mobile = user_detail.get('mobile', '')

        # 4. 查找或创建本地用户
        user = User.query.filter_by(user_name=username).first()

        if not user:
            # 首次登录，自动创建用户
            user = User(
                user_name=username,
                role='user',  # 默认为普通用户
                email=email if user_detail else '',
                status='active'
            )
            # 设置默认密码（防止直接登录）
            user.set_password('dingtalk123')
            db.session.add(user)
            db.session.commit()
            logger.info(f"自动创建钉钉用户: {username}")
        else:
            # 更新最后登录时间
            from datetime import datetime
            user.last_login_time = datetime.now()
            db.session.commit()

        # 5. 生成本地JWT令牌
        user_info_for_token = {
            'userName': user.user_name,
            'realName': real_name,
            'role': user.role
        }
        token = generate_token(user_info_for_token)

        return success_response(data={
            'token': token,
            'tokenType': 'Bearer',
            'expiresIn': 8 * 3600,
            'userInfo': {
                'userName': user.user_name,
                'realName': real_name,
                'role': user.role
            }
        }, message='钉钉免登录成功')

    except Exception as e:
        logger.error(f"钉钉免登录异常: {e}")
        return error_response(2005, f'免登录失败: {str(e)}', http_status=500)


@auth_dingtalk_bp.route('/dingtalk/config', methods=['GET'])
def get_dingtalk_config():
    """
    获取钉钉配置信息（用于前端初始化）
    只返回必要的配置信息，不返回敏感信息
    """
    try:
        app_key = current_app.config.get('DINGTALK_APP_KEY')

        if not app_key:
            return error_response(2006, '钉钉应用未配置', http_status=500)

        return success_response(data={
            'appId': app_key,  # 前端需要使用
            'corpId': current_app.config.get('DINGTALK_CORP_ID', '')
        }, message='获取钉钉配置成功')

    except Exception as e:
        return error_response(2007, f'获取配置失败: {str(e)}', http_status=500)
