"""
通知相关路由：

调度配置（入库，可热重载）
- GET  /notifications/config                  读取调度配置 + 渠道凭证状态
- PUT  /notifications/scheduler/config        修改 cron/enabled/timezone/lookback
- POST /notifications/scheduler/reload        触发调度器立即重新加载（实际生效 ≤60s）

通知测试
- POST /notifications/test                    手动触发一次完整检查 + 通知（admin）

通知记录
- GET  /notifications/logs                    分页查询通知发送日志
- GET  /notifications/logs/by-check/<check_no> 按检查批次查通知日志
- DELETE /notifications/logs/<log_id>         删除单条通知日志
- DELETE /notifications/logs/batch            批量删除通知日志
"""
import logging
from datetime import datetime, timedelta
from types import SimpleNamespace as _SimpleNamespace

from flask import Blueprint, request, current_app

from app.models.db import db
from app.models.notification_log import NotificationLog
from app.models.sys_config import SysConfig
from app.utils.jwt_utils import auth_required
from app.utils.response import success_response, error_response
from app.services.notification_service import (
    run_scheduled_check_and_notify,
    _get_notify_credential,
    _build_notifier_for_channel
)

logger = logging.getLogger(__name__)

notifications_bp = Blueprint('notifications', __name__)


def _admin_only():
    """检查当前用户是否为 admin，否则返回 403。"""
    user = getattr(request, 'current_user', None) or {}
    if user.get('role') != 'admin':
        return error_response(4031, '需要管理员权限', http_status=403)
    return None


def _get_sys_config(key, default=None):
    c = SysConfig.query.filter_by(config_key=key).first()
    return c.config_value if c and c.config_value is not None else default


def _set_sys_config(key, value, *, config_type='string', description='', category='system', is_editable=1):
    """若配置项存在则更新；不存在则新增。

    is_editable=0 用于 secret 类配置（AppSecret/SMTP 密码），
    使其不通过 /system/config 通用查询接口暴露。
    """
    c = SysConfig.query.filter_by(config_key=key).first()
    if c:
        c.config_value = str(value)
    else:
        c = SysConfig(
            config_key=key,
            config_value=str(value),
            config_type=config_type,
            category=category,
            description=description,
            is_editable=is_editable
        )
        db.session.add(c)


def _parse_cron_fields(expr):
    """校验 5 字段 cron 表达式。失败抛 ValueError。"""
    parts = (expr or '').split()
    if len(parts) != 5:
        raise ValueError("cron 表达式必须是 5 字段：分 时 日 月 周")
    return parts


@notifications_bp.route('/notifications/config', methods=['GET'])
@auth_required
def get_notification_config():
    """读取调度配置 + 渠道凭证状态。

    所有字段都走 sys_config 优先 + .env 兜底，保证 admin 改完凭证后
    UI 看到的是最新值。

    返回结构（不包含任何 secret 的明文）：
      schedulerEnabled / schedulerCron / schedulerTimezone / lookbackWeeks / reloadPending
      dingtalk.enabled / dingtalk.configured / dingtalk.corpId / dingtalk.agentId
        / dingtalk.appKey（明文，标识符）/ dingtalk.hasAppSecret（仅布尔）
      email.enabled / email.configured / email.host / email.port / email.useSsl
        / email.fromAddr / email.user（明文）/ email.hasPassword（仅布尔）
    """
    err = _admin_only()
    if err:
        return err

    cfg = current_app.config

    # === 调度配置 ===
    enabled_str = _get_sys_config('scheduler.enabled', 'true')
    cron = _get_sys_config('scheduler.cron', cfg.get('SCHEDULER_CRON', '0 18 * * 1'))
    tz = _get_sys_config('scheduler.timezone', cfg.get('SCHEDULER_TIMEZONE', 'Asia/Shanghai'))
    lookback_str = _get_sys_config('scheduler.lookback_weeks', '2')
    reload_ts = _get_sys_config('scheduler.reload_requested', '')

    try:
        lookback = int(lookback_str)
    except (TypeError, ValueError):
        lookback = 2

    # === 渠道配置（DB 优先 + .env 兜底）===
    dt_corp = _get_notify_credential('notify.dingtalk.corp_id', cfg.get('DINGTALK_CORP_ID', ''))
    dt_agent = _get_notify_credential('notify.dingtalk.agent_id', cfg.get('DINGTALK_AGENT_ID', ''))
    dt_key = _get_notify_credential('notify.dingtalk.app_key', cfg.get('DINGTALK_APP_KEY', ''))
    dt_secret = _get_notify_credential('notify.dingtalk.app_secret', cfg.get('DINGTALK_APP_SECRET', ''))
    dt_enabled_raw = _get_notify_credential(
        'notify.dingtalk.enabled',
        'true' if cfg.get('NOTIFY_DINGTALK') else 'false'
    )

    em_host = _get_notify_credential('notify.email.host', cfg.get('SMTP_HOST', ''))
    em_port_raw = _get_notify_credential('notify.email.port', str(cfg.get('SMTP_PORT', 465)))
    em_user = _get_notify_credential('notify.email.user', cfg.get('SMTP_USER', ''))
    em_pwd = _get_notify_credential('notify.email.password', cfg.get('SMTP_PASSWORD', ''))
    em_ssl_raw = _get_notify_credential(
        'notify.email.use_ssl',
        'true' if cfg.get('SMTP_USE_SSL', True) else 'false'
    )
    em_from = _get_notify_credential('notify.email.from_addr', cfg.get('MAIL_FROM', ''))
    em_enabled_raw = _get_notify_credential(
        'notify.email.enabled',
        'true' if cfg.get('NOTIFY_EMAIL') else 'false'
    )

    try:
        em_port = int(em_port_raw)
    except (TypeError, ValueError):
        em_port = 465

    return success_response(data={
        'schedulerEnabled': (enabled_str or '').lower() == 'true',
        'schedulerCron': cron,
        'schedulerTimezone': tz,
        'lookbackWeeks': lookback,
        'reloadPending': bool(reload_ts),
        'dingtalk': {
            'enabled': dt_enabled_raw.lower() == 'true',
            'configured': bool(dt_corp and dt_agent and dt_key and dt_secret),
            'corpId': dt_corp,
            'agentId': dt_agent,
            'appKey': dt_key,
            'hasAppSecret': bool(dt_secret)
        },
        'email': {
            'enabled': em_enabled_raw.lower() == 'true',
            'configured': bool(em_host and em_user and em_from and em_pwd),
            'host': em_host,
            'port': em_port,
            'useSsl': em_ssl_raw.lower() == 'true',
            'fromAddr': em_from,
            'user': em_user,
            'hasPassword': bool(em_pwd)
        }
    })


@notifications_bp.route('/notifications/scheduler/config', methods=['PUT'])
@auth_required
def update_scheduler_config():
    """更新调度配置。同时写 reload_requested 触发 scheduler 重载。

    请求体：{ enabled?: bool, cron?: str, timezone?: str, lookbackWeeks?: int }
    所有字段可选，仅传哪几项改哪几项。
    """
    err = _admin_only()
    if err:
        return err

    data = request.get_json() or {}

    try:
        if 'cron' in data:
            _parse_cron_fields(data['cron'])  # 校验
            _set_sys_config('scheduler.cron', data['cron'].strip(),
                            config_type='string', description='定时检查 cron 表达式(分 时 日 月 周)')
        if 'enabled' in data:
            _set_sys_config('scheduler.enabled', 'true' if data['enabled'] else 'false',
                            config_type='boolean', description='是否启用定时调度器')
        if 'timezone' in data:
            tz = (data['timezone'] or '').strip() or 'Asia/Shanghai'
            _set_sys_config('scheduler.timezone', tz,
                            config_type='string', description='调度器时区')
        if 'lookbackWeeks' in data:
            n = int(data['lookbackWeeks'])
            if n < 1 or n > 12:
                return error_response(4002, 'lookbackWeeks 必须在 1-12 之间', http_status=400)
            _set_sys_config('scheduler.lookback_weeks', str(n),
                            config_type='number', description='定时检查向前推几周')
    except ValueError as e:
        return error_response(4002, str(e), http_status=400)
    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)

    # 写 reload_requested，scheduler 轮询到时会 reschedule
    _set_sys_config('scheduler.reload_requested', datetime.now().isoformat(),
                    config_type='string', description='调度器重载请求时间戳(内部使用)', category='system')
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)

    return success_response(message='配置已保存，调度器将在 60 秒内自动重载')


@notifications_bp.route('/notifications/scheduler/reload', methods=['POST'])
@auth_required
def reload_scheduler():
    """触发调度器立即重载（实际生效 ≤60s）。"""
    err = _admin_only()
    if err:
        return err
    try:
        _set_sys_config('scheduler.reload_requested', datetime.now().isoformat(),
                        config_type='string', description='调度器重载请求时间戳(内部使用)')
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)
    return success_response(message='重载请求已记录，调度器将在 60 秒内生效')


@notifications_bp.route('/notifications/test', methods=['POST'])
@auth_required
def trigger_notification_test():
    """手动触发一次定时检查 + 通知（admin only）。"""
    err = _admin_only()
    if err:
        return err
    try:
        logger.info(f"管理员 {request.current_user.get('userName')} 手动触发通知测试")
        run_scheduled_check_and_notify()
        return success_response(message='通知测试已执行，请查看后端日志、通知记录页和员工收件情况')
    except Exception as e:
        logger.exception("通知测试失败")
        return error_response(500, str(e), http_status=500)


@notifications_bp.route('/notifications/logs', methods=['GET'])
@auth_required
def list_notification_logs():
    """分页查询通知发送日志。

    查询参数：page, size, channel, status, employeeName, checkNo, startDate, endDate
    """
    err = _admin_only()
    if err:
        return err

    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        channel = (request.args.get('channel') or '').strip()
        status = (request.args.get('status') or '').strip()
        employee_name = (request.args.get('employeeName') or '').strip()
        check_no = (request.args.get('checkNo') or '').strip()
        start_date = (request.args.get('startDate') or '').strip()
        end_date = (request.args.get('endDate') or '').strip()

        query = NotificationLog.query
        if channel:
            query = query.filter(NotificationLog.channel == channel)
        if status:
            query = query.filter(NotificationLog.status == status)
        if employee_name:
            query = query.filter(NotificationLog.employee_name.like(f'%{employee_name}%'))
        if check_no:
            query = query.filter(NotificationLog.check_no == check_no)
        if start_date:
            query = query.filter(NotificationLog.sent_at >= datetime.fromisoformat(start_date))
        if end_date:
            # endDate 当天结束
            end_dt = datetime.fromisoformat(end_date).replace(hour=23, minute=59, second=59)
            query = query.filter(NotificationLog.sent_at <= end_dt)

        pagination = query.order_by(NotificationLog.sent_at.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        return success_response(data={
            'list': [log.to_dict() for log in pagination.items],
            'total': pagination.total,
            'page': page,
            'size': size,
            'totalPages': pagination.pages
        })
    except Exception as e:
        return error_response(500, str(e), http_status=500)


@notifications_bp.route('/notifications/logs/by-check/<check_no>', methods=['GET'])
@auth_required
def list_logs_by_check(check_no):
    """按检查批次查询通知日志。"""
    err = _admin_only()
    if err:
        return err
    try:
        logs = NotificationLog.query.filter_by(check_no=check_no) \
            .order_by(NotificationLog.sent_at.desc()).all()
        return success_response(data={'list': [log.to_dict() for log in logs]})
    except Exception as e:
        return error_response(500, str(e), http_status=500)


@notifications_bp.route('/notifications/logs/<int:log_id>', methods=['DELETE'])
@auth_required
def delete_notification_log(log_id):
    """删除单条通知发送日志。"""
    try:
        log = NotificationLog.query.get(log_id)
        if not log:
            return error_response(7004, '日志不存在', http_status=404)
        db.session.delete(log)
        db.session.commit()
        return success_response(message='删除成功')
    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@notifications_bp.route('/notifications/logs/batch', methods=['DELETE'])
@auth_required
def batch_delete_notification_logs():
    """批量删除通知发送日志。

    请求体：{ ids: [int, ...] }
    """
    try:
        data = request.get_json() or {}
        ids = data.get('ids', [])
        if not ids:
            return error_response(4001, '请选择要删除的日志', http_status=400)
        logs = NotificationLog.query.filter(NotificationLog.id.in_(ids)).all()
        if not logs:
            return error_response(7004, '日志不存在', http_status=404)
        for log in logs:
            db.session.delete(log)
        db.session.commit()
        return success_response(message=f'成功删除 {len(logs)} 条日志')
    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e), http_status=500)


@notifications_bp.route('/notifications/channels/dingtalk', methods=['PUT'])
@auth_required
def update_dingtalk_config():
    """更新钉钉渠道配置。

    请求体字段全部可选（仅传哪项改哪项）：
      enabled: bool
      corpId: str
      agentId: str
      appKey: str （非空才覆盖）
      appSecret: str （非空才覆盖；空值/缺省 = 保持不变）
    """
    err = _admin_only()
    if err:
        return err

    data = request.get_json() or {}

    try:
        if 'enabled' in data:
            _set_sys_config('notify.dingtalk.enabled',
                            'true' if data['enabled'] else 'false',
                            config_type='boolean', description='是否启用钉钉通知',
                            category='notify')
        if 'corpId' in data:
            _set_sys_config('notify.dingtalk.corp_id', (data['corpId'] or '').strip(),
                            description='钉钉 CorpID', category='notify')
        if 'agentId' in data:
            _set_sys_config('notify.dingtalk.agent_id', str(data['agentId'] or '').strip(),
                            description='钉钉 AgentId', category='notify')
        if 'appKey' in data and (data['appKey'] or '').strip():
            _set_sys_config('notify.dingtalk.app_key', data['appKey'].strip(),
                            description='钉钉 AppKey', category='notify')
        if 'appSecret' in data and (data['appSecret'] or '').strip():
            _set_sys_config('notify.dingtalk.app_secret', data['appSecret'].strip(),
                            description='钉钉 AppSecret', category='notify', is_editable=0)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception("保存钉钉配置失败")
        return error_response(500, str(e), http_status=500)

    return success_response(message='钉钉配置已保存')


@notifications_bp.route('/notifications/channels/email', methods=['PUT'])
@auth_required
def update_email_config():
    """更新邮件渠道配置。

    请求体字段全部可选：
      enabled / host / port(int) / useSsl(bool) / user / fromAddr
      password: str （非空才覆盖；空值/缺省 = 保持不变）
    """
    err = _admin_only()
    if err:
        return err

    data = request.get_json() or {}

    try:
        if 'enabled' in data:
            _set_sys_config('notify.email.enabled',
                            'true' if data['enabled'] else 'false',
                            config_type='boolean', description='是否启用邮件通知',
                            category='notify')
        if 'host' in data:
            _set_sys_config('notify.email.host', (data['host'] or '').strip(),
                            description='SMTP 主机', category='notify')
        if 'port' in data:
            _set_sys_config('notify.email.port', str(int(data['port'])),
                            config_type='number', description='SMTP 端口', category='notify')
        if 'useSsl' in data:
            _set_sys_config('notify.email.use_ssl',
                            'true' if data['useSsl'] else 'false',
                            config_type='boolean', description='是否使用 SSL', category='notify')
        if 'user' in data:
            _set_sys_config('notify.email.user', (data['user'] or '').strip(),
                            description='SMTP 登录账号', category='notify')
        if 'fromAddr' in data:
            _set_sys_config('notify.email.from_addr', (data['fromAddr'] or '').strip(),
                            description='发件人地址', category='notify')
        if 'password' in data and (data['password'] or '').strip():
            _set_sys_config('notify.email.password', data['password'].strip(),
                            description='SMTP 登录密码', category='notify', is_editable=0)
        db.session.commit()
    except (TypeError, ValueError) as e:
        db.session.rollback()
        return error_response(4002, f'字段类型错误: {e}', http_status=400)
    except Exception as e:
        db.session.rollback()
        logger.exception("保存邮件配置失败")
        return error_response(500, str(e), http_status=500)

    return success_response(message='邮件配置已保存')


@notifications_bp.route('/notifications/channels/<channel>/test', methods=['POST'])
@auth_required
def test_channel(channel):
    """对单个渠道发送一条测试消息，验证凭证是否正确。

    请求体：{ target: str }  手机号（钉钉）或邮箱（邮件）
    会真实发送，请告知用户。
    """
    err = _admin_only()
    if err:
        return err

    if channel not in ('dingtalk', 'email'):
        return error_response(4002, '未知渠道', http_status=400)

    data = request.get_json() or {}
    target = (data.get('target') or '').strip()
    if not target:
        return error_response(4002, '请提供测试接收方（手机号/邮箱）', http_status=400)

    notifier = _build_notifier_for_channel(channel)
    if not notifier:
        return error_response(4003, '凭证不全，无法测试，请先完整填写并保存', http_status=400)

    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    fake_employee = _SimpleNamespace(
        employee_name='测试接收人',
        dept_name='系统设置',
        phone=target if channel == 'dingtalk' else '',
        email=target if channel == 'email' else ''
    )
    test_payload = [{
        'issueType': 'missing',
        'deptName': '系统设置',
        'userName': '测试接收人',
        'gapStartDate': week_start.isoformat(),
        'gapEndDate': week_end.isoformat(),
        'affectedWorkdays': 1,
        'description': '这是来自系统设置页面的测试通知，用于验证渠道配置是否正确。'
    }]

    try:
        notifier.notify(
            employee=fake_employee,
            dept_name='系统设置',
            week_start=week_start,
            week_end=week_end,
            missing_details=test_payload
        )
        return success_response(message=f'测试消息已发送至 {target}')
    except Exception as e:
        logger.exception(f"渠道 {channel} 测试失败")
        return error_response(5003, f'发送失败: {e}', http_status=500)
