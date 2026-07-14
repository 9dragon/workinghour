"""
通知发送方抽象基类。

每个渠道（钉钉/邮件）实现一个子类，notify() 完成单员工单次发送。
失败时记录日志但不抛出，避免影响其他员工。
"""
import logging

logger = logging.getLogger(__name__)


class BaseNotifier:
    name = 'base'

    def notify(self, *, employee, dept_name, week_start, week_end, missing_details):
        """发送通知。

        参数：
            employee:        Employee ORM 对象（含 employee_name, phone, email 等）
            dept_name:       str, 部门名
            week_start:      datetime.date, 目标周周一
            week_end:        datetime.date, 目标周周日
            missing_details: list[dict], 该员工的 missing 详情条目（issueType='missing'）

        返回值：
            str:  实际渲染并发送的消息体（钉钉=markdown 文本，邮件=HTML 源码），
                  调用方用于写入 notification_logs.content 供事后审计。
            None: 因联系信息缺失等理由在 notifier 内部跳过，未实际发送。
        """
        raise NotImplementedError
