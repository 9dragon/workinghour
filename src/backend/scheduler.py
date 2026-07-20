"""
定时调度器入口（独立进程）。

部署方式：
    python scheduler.py

或 docker-compose / k8s 中作为独立 service 运行。
与 web (gunicorn) 进程完全隔离，避免多 worker 重复执行同一任务。

配置优先级（高 → 低）：
    1. sys_config 表中的 scheduler.enabled / scheduler.cron / scheduler.timezone
       （管理后台可热修改，60 秒内生效）
    2. .env / 环境变量 SCHEDULER_ENABLED / SCHEDULER_CRON / SCHEDULER_TIMEZONE
       （首次启动时若 DB 无配置则兜底）

热重载机制：
    进程内启动 60 秒轮询 job `config_watcher`，对比当前运行参数与 DB 最新值，
    发现变化即 reschedule 主任务；scheduler.reload_requested 时间戳作为强制信号。
"""
import logging
import os
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app import create_app
from app.models.db import db
from app.models.sys_config import SysConfig
from app.services.notification_service import run_scheduled_check_and_notify

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('scheduler')

JOB_ID = 'weekly_integrity_check'
DEFAULT_CRON = '0 18 * * 1'
DEFAULT_TZ = 'Asia/Shanghai'


_DOW_ALIASES = {'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'}


def _convert_dow_to_aps(expr):
    """把 day_of_week 字段从 Linux cron 习惯转成 APScheduler 习惯。

    必要性：APScheduler 的 DayOfWeekField.get_value 返回 dateval.weekday()
    （0=Mon..6=Sun），而 Linux cron / crontab(5) / 前端 UI 都按
    0=Sun, 1=Mon, ..., 5=Fri, 6=Sat, 7=Sun。两套编码差一天。

    若不做转换，DB 存的 `0 18 * * 1`（用户期望周一）会被 APScheduler
    解释成周二触发。

    转换规则：linux_n -> (linux_n - 1) % 7
        0(Sun)->6   1(Mon)->0   5(Fri)->4   6(Sat)->5   7(Sun)->6

    支持 *, 别名(mon..sun), 数字, 范围(1-5), 列表(1,3,5), 步长(*/2, 1-5/2)。
    """
    if not expr or expr == '*':
        return expr

    def convert_token(tok):
        tok = tok.strip().lower()
        if not tok or tok == '*':
            return tok
        if tok in _DOW_ALIASES:
            return tok
        if '/' in tok:
            base, step = tok.split('/', 1)
            if base == '*':
                return tok
            return f'{convert_token(base)}/{step}'
        if '-' in tok:
            lo, hi = tok.split('-', 1)
            try:
                return f'{(int(lo) - 1) % 7}-{(int(hi) - 1) % 7}'
            except ValueError:
                return tok
        try:
            return str((int(tok) - 1) % 7)
        except ValueError:
            return tok

    return ','.join(convert_token(p) for p in expr.split(','))


def _parse_cron(expr, tz=None):
    """解析 5 字段 cron 表达式为 CronTrigger。失败抛 ValueError。

    tz 必须在构造函数里传入——直接给 trigger.timezone 赋字符串值会绕过
    APScheduler 的时区对象转换，触发 'tzinfo argument must be ... not str'。

    day_of_week 按 Linux cron 习惯解释（0/7=Sun, 1=Mon, ..., 6=Sat），
    内部转成 APScheduler 的 0=Mon..6=Sun。DB 与 UI 永远存 Linux cron 形式。
    """
    parts = (expr or '').split()
    if len(parts) != 5:
        raise ValueError(f"cron 表达式必须是 5 字段（分 时 日 月 周），当前: {expr!r}")
    return CronTrigger(
        minute=parts[0], hour=parts[1], day=parts[2],
        month=parts[3],
        day_of_week=_convert_dow_to_aps(parts[4]),
        timezone=tz
    )


def _get_sys_config(key, default=None):
    """读 sys_config 单条。"""
    c = SysConfig.query.filter_by(config_key=key).first()
    if c and c.config_value is not None and c.config_value != '':
        return c.config_value
    return default


def _read_scheduler_config(app):
    """从 DB 读取调度配置，DB 无值则用 .env / 环境变量兜底。"""
    cfg = app.config
    enabled_raw = _get_sys_config(
        'scheduler.enabled',
        os.environ.get('SCHEDULER_ENABLED', cfg.get('SCHEDULER_ENABLED', 'true'))
    )
    cron = _get_sys_config(
        'scheduler.cron',
        os.environ.get('SCHEDULER_CRON', cfg.get('SCHEDULER_CRON', DEFAULT_CRON))
    )
    tz = _get_sys_config(
        'scheduler.timezone',
        os.environ.get('SCHEDULER_TIMEZONE', cfg.get('SCHEDULER_TIMEZONE', DEFAULT_TZ))
    )
    reload_ts = _get_sys_config('scheduler.reload_requested', '')

    return {
        'enabled': (enabled_raw or '').lower() == 'true',
        'cron': cron or DEFAULT_CRON,
        'tz': tz or DEFAULT_TZ,
        'reload_requested': reload_ts or ''
    }


def _reschedule_if_changed(scheduler, app, state):
    """对比当前调度状态与 DB 最新值，发现变化则 reschedule。"""
    with app.app_context():
        try:
            latest = _read_scheduler_config(app)
        except Exception:
            logger.exception("读取调度配置失败，本次跳过")
            return

    # 1. reload_requested 强制 reschedule（即使配置看似没变）
    force = bool(latest['reload_requested']) and latest['reload_requested'] != state.get('last_reload_seen')

    # 2. 关键参数变化 → reschedule
    changed = (
        latest['enabled'] != state.get('enabled')
        or latest['cron'] != state.get('cron')
        or latest['tz'] != state.get('tz')
    )

    if not force and not changed:
        return

    logger.info(
        f"检测到配置变化或重载请求: enabled={latest['enabled']} "
        f"cron={latest['cron']!r} tz={latest['tz']!r} reload_requested={latest['reload_requested']!r}"
    )

    # 移除现有 job
    try:
        scheduler.remove_job(JOB_ID)
    except Exception:
        pass  # job 不存在是正常情况（首次启动 / enabled 刚从 false 切回）

    if not latest['enabled']:
        logger.info("scheduler.enabled=false，主任务保持暂停状态")
    else:
        try:
            trigger = _parse_cron(latest['cron'], latest['tz'])
        except ValueError as e:
            logger.error(f"cron 解析失败，保持已移除状态: {e}")
            # 不更新 state.last_reload_seen，让下一次轮询再尝试
            return

        scheduler.add_job(
            _make_job(app),
            trigger=trigger,
            id=JOB_ID,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=3600,
            replace_existing=True
        )
        logger.info(f"主任务已重新调度: cron={latest['cron']!r} tz={latest['tz']!r}")

    # 更新内存状态
    state['enabled'] = latest['enabled']
    state['cron'] = latest['cron']
    state['tz'] = latest['tz']
    state['last_reload_seen'] = latest['reload_requested']


def _make_job(app):
    """构造主任务闭包。"""
    def job():
        with app.app_context():
            try:
                logger.info("=== 定时周报检查开始 ===")
                run_scheduled_check_and_notify()
                logger.info("=== 定时周报检查结束 ===")
            except Exception:
                logger.exception("定时周报检查执行失败")
    return job


def main():
    app = create_app()

    # 初始读取配置（带 app_context）
    with app.app_context():
        db.create_all()
        initial = _read_scheduler_config(app)

    if not initial['enabled']:
        logger.info("初始配置 scheduler.enabled=false，调度器仍启动以便接收后续启用信号")

    state = {
        'enabled': None,        # 强制首次 reschedule
        'cron': None,
        'tz': None,
        'last_reload_seen': None
    }

    scheduler = BlockingScheduler(timezone=initial['tz'])

    # 首次调度（与热重载用同一逻辑，保证一致性）
    _reschedule_if_changed(scheduler, app, state)

    # 60 秒轮询 job：检测配置变化 / reload 信号
    scheduler.add_job(
        lambda: _reschedule_if_changed(scheduler, app, state),
        trigger='interval',
        seconds=60,
        id='config_watcher',
        coalesce=True,
        max_instances=1,
        replace_existing=True
    )
    logger.info("config_watcher 已启动，每 60 秒检查一次配置变更")

    logger.info(
        f"调度器启动: enabled={initial['enabled']} cron={initial['cron']!r} tz={initial['tz']!r}"
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("调度器收到退出信号，关闭")
        scheduler.shutdown(wait=False)


if __name__ == '__main__':
    main()
