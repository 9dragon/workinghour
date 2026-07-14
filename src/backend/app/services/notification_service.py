"""
定时检查 + 通知编排。

run_scheduled_check_and_notify() 是调度器入口：
1. 计算目标周（默认本周往前推 N 周，N 来自 sys_config.scheduler.lookback_weeks）
2. 调用 check_service.run_integrity_check 跑完整性检查
3. 按 user 聚合 missing 详情
4. 按 .env 启用的渠道构造 Notifier 列表
5. 逐员工发送；单员工失败不影响其他人
6. 每次发送都写 NotificationLog（success/failed/skipped）
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta

from flask import current_app

from app.models.db import db
from app.models.employee import Employee
from app.models.notification_log import NotificationLog
from app.models.sys_config import SysConfig
from app.services.check_service import run_integrity_check
from app.services.notifier.dingtalk import DingTalkNotifier
from app.services.notifier.email_notifier import EmailNotifier

logger = logging.getLogger(__name__)


def _get_lookback_weeks():
    cfg = SysConfig.query.filter_by(config_key='scheduler.lookback_weeks').first()
    if cfg:
        try:
            n = int(cfg.config_value)
            if n >= 1:
                return n
        except (TypeError, ValueError):
            pass
    return 2


def _compute_target_week(lookback_weeks, today=None):
    """计算目标周的周一、周日。

    规则：以"本周一"为锚点，往前推 lookback_weeks 周。
    例：今天是周三，lookback_weeks=2 → 目标周 = 上上周的周一到周日。
    """
    today = today or datetime.now().date()
    this_monday = today - timedelta(days=today.weekday())  # weekday()=0 表示周一
    target_monday = this_monday - timedelta(weeks=lookback_weeks)
    target_sunday = target_monday + timedelta(days=6)
    return target_monday, target_sunday


def _get_notify_credential(db_key, env_default):
    """DB 优先，.env 兜底。返回字符串。

    sys_config 有值就用 DB 的；没值或空串就用 .env 兜底。
    一旦 admin 通过 UI 保存过，DB 就有值，永久覆盖 .env。
    """
    c = SysConfig.query.filter_by(config_key=db_key).first()
    if c is not None and c.config_value is not None:
        return c.config_value
    return env_default


def _build_notifier_for_channel(channel):
    """构造单个 channel 的 notifier，忽略 enabled 开关。

    凭证不全返回 None。供 _build_enabled_notifiers 和测试接口共用，
    保证两条路径用同一份"凭证完整度"判定逻辑。
    """
    cfg = current_app.config
    if channel == 'dingtalk':
        corp_id = _get_notify_credential('notify.dingtalk.corp_id', cfg.get('DINGTALK_CORP_ID', ''))
        agent_id = _get_notify_credential('notify.dingtalk.agent_id', cfg.get('DINGTALK_AGENT_ID', ''))
        app_key = _get_notify_credential('notify.dingtalk.app_key', cfg.get('DINGTALK_APP_KEY', ''))
        app_secret = _get_notify_credential('notify.dingtalk.app_secret', cfg.get('DINGTALK_APP_SECRET', ''))
        if not (corp_id and agent_id and app_key and app_secret):
            return None
        return DingTalkNotifier(
            corp_id=corp_id, agent_id=agent_id,
            app_key=app_key, app_secret=app_secret
        )
    if channel == 'email':
        host = _get_notify_credential('notify.email.host', cfg.get('SMTP_HOST', ''))
        port_raw = _get_notify_credential('notify.email.port', str(cfg.get('SMTP_PORT', 465)))
        user = _get_notify_credential('notify.email.user', cfg.get('SMTP_USER', ''))
        password = _get_notify_credential('notify.email.password', cfg.get('SMTP_PASSWORD', ''))
        use_ssl_raw = _get_notify_credential(
            'notify.email.use_ssl',
            'true' if cfg.get('SMTP_USE_SSL', True) else 'false'
        )
        from_addr = _get_notify_credential('notify.email.from_addr', cfg.get('MAIL_FROM', ''))
        if not (host and user and from_addr):
            return None
        try:
            port = int(port_raw)
        except (TypeError, ValueError):
            port = 465
        return EmailNotifier(
            host=host, port=port, user=user, password=password,
            use_ssl=(use_ssl_raw.lower() == 'true'), from_addr=from_addr
        )
    return None


def _build_enabled_notifiers():
    """根据 DB 配置（.env 兜底）构造已启用的 Notifier 列表。

    每次调用都从 DB 现读，因此调度器每次 fire 都会拿到最新凭证，
    无需触发 reload。
    """
    cfg = current_app.config
    result = []

    dt_enabled_raw = _get_notify_credential(
        'notify.dingtalk.enabled',
        'true' if cfg.get('NOTIFY_DINGTALK') else 'false'
    )
    if dt_enabled_raw.lower() == 'true':
        n = _build_notifier_for_channel('dingtalk')
        if n:
            result.append(n)
        else:
            logger.info("钉钉已启用但凭证不全，跳过 DingTalkNotifier")

    em_enabled_raw = _get_notify_credential(
        'notify.email.enabled',
        'true' if cfg.get('NOTIFY_EMAIL') else 'false'
    )
    if em_enabled_raw.lower() == 'true':
        n = _build_notifier_for_channel('email')
        if n:
            result.append(n)
        else:
            logger.info("邮件已启用但配置不全，跳过 EmailNotifier")

    return result


def run_scheduled_check_and_notify():
    """调度器入口：跑检查 → 按员工分发通知。"""
    lookback = _get_lookback_weeks()
    week_start, week_end = _compute_target_week(lookback)
    logger.info(f"开始定时检查，目标周: {week_start} ~ {week_end} (lookback={lookback})")

    check_no, summary, details = run_integrity_check(
        start_date=week_start.isoformat(),
        end_date=week_end.isoformat(),
        trigger_type='scheduled',
        check_user='system'
    )
    logger.info(
        f"检查完成 check_no={check_no} total={summary['totalUsers']} "
        f"missing={summary['missingUsers']} duplicate={summary['duplicateUsers']}"
    )

    per_user = defaultdict(list)
    user_dept = {}
    for d in details:
        if d.get('issueType') == 'missing':
            per_user[d['userName']].append(d)
            user_dept[d['userName']] = d.get('deptName', '')

    if not per_user:
        logger.info("本次检查无未提交员工，不发送任何通知")
        return

    notifiers = _build_enabled_notifiers()
    if not notifiers:
        logger.warning("无可用通知渠道，仅完成检查记录，未发送通知")
        return

    sent_count = 0
    skip_count = 0
    fail_count = 0
    for user_name, items in per_user.items():
        employee = Employee.query.filter_by(employee_name=user_name).first()
        dept = user_dept.get(user_name, '')

        if not employee:
            _log(check_no, user_name, dept, None, 'skipped', '员工档案未找到')
            logger.warning(f"员工 {user_name} 在 employees 表中找不到，跳过通知")
            skip_count += 1
            continue
        if not (employee.phone or employee.email):
            _log(check_no, user_name, dept, None, 'skipped', '无手机号且无邮箱')
            logger.warning(f"员工 {user_name} 既无手机号也无邮箱，跳过通知")
            skip_count += 1
            continue

        for notifier in notifiers:
            channel = notifier.name
            # 渠道与联系信息匹配：无手机号不能发钉钉；无邮箱不能发邮件
            if channel == 'dingtalk' and not (employee.phone or '').strip():
                _log(check_no, user_name, dept, channel, 'skipped', '无手机号')
                continue
            if channel == 'email' and not (employee.email or '').strip():
                _log(check_no, user_name, dept, channel, 'skipped', '无邮箱')
                continue
            try:
                content = notifier.notify(
                    employee=employee,
                    dept_name=dept,
                    week_start=week_start,
                    week_end=week_end,
                    missing_details=items
                )
                _log(check_no, user_name, dept, channel, 'success', None, content=content)
            except Exception as e:
                _log(check_no, user_name, dept, channel, 'failed', str(e))
                logger.exception(f"通知失败 via={channel} user={user_name}")
                fail_count += 1
                continue
        sent_count += 1

    logger.info(
        f"通知分发完成: 应通知 {len(per_user)} 人，发送 {sent_count} 人，"
        f"跳过 {skip_count} 人，失败 {fail_count} 次"
    )


def _log(check_no, name, dept, channel, status, err, content=None):
    """写一条通知日志。失败不抛出，仅记录。"""
    try:
        db.session.add(NotificationLog(
            check_no=check_no,
            employee_name=name,
            dept_name=dept,
            channel=channel,
            status=status,
            error_message=(err or '')[:1000] or None,
            content=content
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception(f"写 NotificationLog 失败（静默忽略）")
