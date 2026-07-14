"""
钉钉企业应用工作通知。

发送流程：
1. 用 app_key/app_secret 换取 access_token（7200s 有效，模块级缓存）
2. 用员工手机号调 user/getbymobile 取 userId（进程内缓存）
3. 调 corpconversation/asyncsend_v2 发送 markdown 工作通知
   （旧名 corpmessage 已废弃，会报 errcode=22 "不合法 ApiName"）

注意：本模块依赖 requests（已在 requirements.txt）。
"""
import logging
import time

import requests

from .base import BaseNotifier

logger = logging.getLogger(__name__)

DINGTALK_HOST = 'https://oapi.dingtalk.com'

# access_token 相关错误码：缓存里可能持有"我们觉得有效、但钉钉侧已失效"的 token
# （常见于 token 在别处被刷出、应用被调整权限、管理后台改过 secret 等），
# 遇到这些 errcode 时强制刷新一次再重试，避免在缓存 TTL 内持续失败。
TOKEN_INVALID_ERRCODES = {40001, 40014, 42001, 7201}

# 模块级缓存（进程内）
_access_token_cache = {'value': None, 'expires_at': 0}
_userid_cache = {}  # phone -> userId


class DingTalkNotifier(BaseNotifier):
    name = 'dingtalk'

    def __init__(self, *, corp_id, agent_id, app_key, app_secret):
        self.corp_id = corp_id
        self.agent_id = agent_id
        self.app_key = app_key
        self.app_secret = app_secret

    def _get_access_token(self, *, force_refresh=False):
        """获取 access_token，带缓存。失效或为空时重新拉取。

        force_refresh=True 时无条件重新拉取，用于遇到 TOKEN_INVALID_ERRCODES
        时丢弃可能已经被钉钉服务端失效的缓存 token。
        """
        now = time.time()
        if not force_refresh and _access_token_cache['value'] and _access_token_cache['expires_at'] > now + 60:
            return _access_token_cache['value']

        resp = requests.get(
            f'{DINGTALK_HOST}/gettoken',
            params={'appkey': self.app_key, 'appsecret': self.app_secret},
            timeout=10
        )
        data = resp.json()
        if data.get('errcode') != 0:
            raise RuntimeError(f"钉钉 gettoken 失败: {data}")
        token = data['access_token']
        _access_token_cache['value'] = token
        _access_token_cache['expires_at'] = now + data.get('expires_in', 7200)
        return token

    def _get_userid_by_mobile(self, mobile):
        """手机号 -> userId，进程内缓存。失败返回 None。

        遇到 token 类 errcode 会强制刷新一次再重试，避免缓存 token
        在钉钉侧已失效但本地仍在 TTL 内持续返回错误。
        """
        if not mobile:
            return None
        if mobile in _userid_cache:
            return _userid_cache[mobile]

        token = self._get_access_token()
        data = self._call_get_user_by_mobile(token, mobile)

        if data.get('errcode') in TOKEN_INVALID_ERRCODES:
            logger.warning(f"getbymobile 触发 token 重刷 mobile={mobile} errcode={data.get('errcode')}")
            token = self._get_access_token(force_refresh=True)
            data = self._call_get_user_by_mobile(token, mobile)

        if data.get('errcode') != 0:
            logger.warning(f"钉钉手机号查 userId 失败 mobile={mobile}: {data}")
            return None
        user_id = data['result'].get('userid')
        if user_id:
            _userid_cache[mobile] = user_id
        return user_id

    @staticmethod
    def _call_get_user_by_mobile(token, mobile):
        resp = requests.post(
            f'{DINGTALK_HOST}/topapi/v2/user/getbymobile',
            params={'access_token': token},
            json={'mobile': mobile},
            timeout=10
        )
        return resp.json()

    def notify(self, *, employee, dept_name, week_start, week_end, missing_details):
        mobile = (employee.phone or '').strip()
        if not mobile:
            raise ValueError(f"员工 {getattr(employee, 'employee_name', '?')} 无手机号，无法发钉钉")

        user_id = self._get_userid_by_mobile(mobile)
        if not user_id:
            raise RuntimeError(
                f"钉钉未能通过手机号 {mobile} 解析 userId（{getattr(employee, 'employee_name', '?')}）。"
                "常见原因：手机号未加入企业通讯录 / 应用缺少通讯录权限 / 钉钉侧应用配置变更"
            )

        markdown = self._build_markdown(
            name=employee.employee_name,
            dept=dept_name,
            week_start=week_start,
            week_end=week_end,
            details=missing_details
        )

        token = self._get_access_token()
        payload = {
            'agent_id': self.agent_id,
            'userid_list': user_id,
            'msg': {
                'msgtype': 'markdown',
                'markdown': markdown
            }
        }
        resp = requests.post(
            f'{DINGTALK_HOST}/topapi/message/corpconversation/asyncsend_v2',
            params={'access_token': token},
            json=payload,
            timeout=10
        )
        data = resp.json()

        if data.get('errcode') in TOKEN_INVALID_ERRCODES:
            logger.warning(f"asyncsend 触发 token 重刷 user={employee.employee_name} errcode={data.get('errcode')}")
            token = self._get_access_token(force_refresh=True)
            resp = requests.post(
                f'{DINGTALK_HOST}/topapi/message/corpconversation/asyncsend_v2',
                params={'access_token': token},
                json=payload,
                timeout=10
            )
            data = resp.json()

        if data.get('errcode') != 0:
            raise RuntimeError(f"钉钉发送失败 {employee.employee_name}: {data}")
        logger.info(f"钉钉通知已发送: {employee.employee_name} (task_id={data.get('task_id')})")
        return markdown['text']

    @staticmethod
    def _build_markdown(*, name, dept, week_start, week_end, details):
        """构造 markdown 消息体（钉钉 markdown 格式）。"""
        total_days = sum(d['affectedWorkdays'] for d in details)
        lines = [
            f"### 周报提交提醒",
            f"",
            f"**姓名**: {name}    **部门**: {dept}",
            f"",
            f"在 **{week_start} ~ {week_end}** 期间，你有 **{total_days} 个工作日** 未提交周报：",
            f"",
        ]
        for d in details:
            for date_str in d.get('missingDates', []):
                lines.append(f"- {date_str}")
        lines.append("")
        lines.append("请尽快补交。")
        return {'title': '周报提交提醒', 'text': '\n'.join(lines)}
