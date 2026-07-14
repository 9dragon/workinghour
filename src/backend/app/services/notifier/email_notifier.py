"""
SMTP 邮件通知。

支持 SSL（端口 465）或 STARTTLS（端口 587）。
HTML 格式，含一个表格列出 missingDates。
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from .base import BaseNotifier

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    name = 'email'

    def __init__(self, *, host, port, user, password, use_ssl=True, from_addr=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.use_ssl = use_ssl
        self.from_addr = from_addr or user

    def notify(self, *, employee, dept_name, week_start, week_end, missing_details):
        to_addr = (employee.email or '').strip()
        if not to_addr:
            logger.info(f"员工 {employee.employee_name} 无邮箱，跳过邮件通知")
            return

        subject = f"[周报提醒] {week_start} ~ {week_end} 未提交周报"
        html = self._build_html(
            name=employee.employee_name,
            dept=dept_name,
            week_start=week_start,
            week_end=week_end,
            details=missing_details
        )

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.from_addr
        msg['To'] = to_addr
        msg.attach(MIMEText(html, 'html', 'utf-8'))

        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.host, self.port, timeout=15) as smtp:
                    smtp.login(self.user, self.password)
                    smtp.sendmail(self.from_addr, [to_addr], msg.as_string())
            else:
                with smtplib.SMTP(self.host, self.port, timeout=15) as smtp:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.ehlo()
                    smtp.login(self.user, self.password)
                    smtp.sendmail(self.from_addr, [to_addr], msg.as_string())
            logger.info(f"邮件已发送: {employee.employee_name} -> {to_addr}")
            return html
        except smtplib.SMTPAuthenticationError as e:
            logger.exception(f"SMTP 认证失败 {employee.employee_name} ({to_addr}): {e}")
            # 526 是腾讯企业邮/QQ 邮箱自定义的"认证失败"码，标准码为 535
            raise _AuthError(self.host, self.user, e) from e
        except smtplib.SMTPException as e:
            logger.exception(f"SMTP 协议错误 {employee.employee_name} ({to_addr}): {e}")
            raise
        except Exception as e:
            logger.exception(f"邮件发送失败 {employee.employee_name} ({to_addr}): {e}")
            raise

    @staticmethod
    def _build_html(*, name, dept, week_start, week_end, details):
        total_days = sum(d['affectedWorkdays'] for d in details)
        rows = []
        for d in details:
            for date_str in d.get('missingDates', []):
                rows.append(f"<tr><td>{escape(date_str)}</td></tr>")

        return f"""
        <html><body style="font-family: 'Microsoft YaHei', Arial, sans-serif; color: #333;">
          <h3>周报提交提醒</h3>
          <p><b>姓名</b>: {escape(name)} &nbsp;&nbsp; <b>部门</b>: {escape(dept)}</p>
          <p>在 <b>{week_start} ~ {week_end}</b> 期间，你有 <b style="color:#e53935">{total_days}</b> 个工作日未提交周报：</p>
          <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
            <tr style="background:#f5f5f5;"><th>未提交日期</th></tr>
            {''.join(rows)}
          </table>
          <p style="margin-top: 16px;">请尽快补交。</p>
        </body></html>
        """


class _AuthError(Exception):
    """SMTP 认证失败的友好错误，附带 provider 特定的提示。"""

    def __init__(self, host, user, smtp_err):
        code = getattr(smtp_err, 'smtp_code', None) or 0
        self.host = host
        self.user = user
        self.smtp_code = code
        self.smtp_msg = getattr(smtp_err, 'smtp_error', b'') or b''
        if isinstance(self.smtp_msg, bytes):
            try:
                self.smtp_msg = self.smtp_msg.decode('utf-8', errors='replace')
            except Exception:
                self.smtp_msg = str(self.smtp_msg)

    def __str__(self):
        hints = self._hints()
        return (
            f"SMTP 认证失败 (code={self.smtp_code}): {self.smtp_msg} | "
            f"host={self.host} user={self.user} | 排查建议: {hints}"
        )

    def _hints(self):
        h = (self.host or '').lower()
        if 'aliyun' in h:
            return (
                "阿里云企业邮箱：1) 用户名必须是完整邮箱地址（如 dev@yourdomain.com），"
                "密码就是邮箱登录密码（阿里云企业邮无需授权码）；2) 推荐 SSL 端口 465 + "
                "SSL=true；如用 587 必须把 SSL 关闭走 STARTTLS；3) 登录阿里云邮箱管理后台"
                "（qiye.aliyun.com）→ 选中员工 → 确认账号已激活且未禁用；4) 新创建的邮箱"
                "需先用网页登录一次激活；5) 若仍失败，可能密码被改或账号被冻结，重置密码后重试。"
            )
        if 'qq.com' in h or 'tencent' in h or 'exmail' in h:
            return (
                "腾讯企业邮/QQ 邮箱：1) 登录网页邮箱 → 设置 → 客户端专用密码（或账号安全 → "
                "生成授权码），用授权码替代登录密码；2) 确认已开启 SMTP/客户端服务；"
                "3) 端口与 SSL：465 + SSL=true 或 587 + SSL=false（STARTTLS）。"
            )
        if '163.com' in h or 'netease' in h:
            return (
                "网易邮箱：登录网页邮箱 → 设置 → POP3/SMTP/IMAP → 开启 SMTP 服务并"
                "生成客户端授权密码，用此授权密码替代登录密码。"
            )
        if 'gmail' in h:
            return (
                "Gmail：必须使用 App Password（账号设置 → 两步验证 → 应用专用密码），"
                "而非账户登录密码。"
            )
        return (
            "1) 用户名应为完整邮箱地址；2) 部分服务商要求授权码或客户端专用密码而非登录"
            "密码；3) 端口与 SSL 必须匹配：465 + SSL=true，或 587 + SSL=false（STARTTLS）；"
            "4) 确认邮箱已开启 SMTP 服务。"
        )
