"""
utils/mailer.py
邮件发送工具
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

logger = logging.getLogger(__name__)


def send_html_email(
    sender: str,
    password: str,
    recipients: List[str],
    subject: str,
    html_body: str,
    smtp_host: str = "smtp.qq.com",
    smtp_port: int = 465,
) -> bool:
    """
    发送 HTML 邮件
    
    Args:
        sender: 发件人邮箱
        password: SMTP 授权码
        recipients: 收件人列表
        subject: 邮件主题
        html_body: HTML 正文
        smtp_host: SMTP 服务器
        smtp_port: SMTP 端口
    
    Returns:
        bool: 发送是否成功
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        
        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(html_part)
        
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
        
        logger.info(f"✅ 邮件发送成功: {recipients}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 邮件发送失败: {e}")
        return False
