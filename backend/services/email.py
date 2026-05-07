import asyncio
from core.config import settings
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger

class EmailService:
    @staticmethod
    async def send_reset_password_email(email: str, token: str):
        smtp_host = getattr(settings, "SMTP_HOST", None)
        smtp_port_raw = getattr(settings, "SMTP_PORT", None)
        smtp_port = int(smtp_port_raw) if smtp_port_raw else None
        smtp_user = getattr(settings, "SMTP_USER", None)
        smtp_pass = getattr(settings, "SMTP_PASS", None)
        sender_email = getattr(settings, "SENDER_EMAIL", None)
        sender_name = getattr(settings, "SENDER_NAME", None)

        subject = "Mã xác thực khôi phục mật khẩu - DocLib"
        body = f"""Chào bạn,
Chúng tôi nhận được yêu cầu khôi phục mật khẩu cho tài khoản {email}.
Mã xác thực của bạn là: {token}
Lưu ý: Mã này chỉ có hiệu lực trong vòng 10 phút. Nếu bạn không yêu cầu thay đổi này, vui lòng bỏ qua email này.
Trân trọng,
Đội ngũ DocLib."""

        if not all([smtp_host, smtp_port, smtp_user, smtp_pass, sender_email, sender_name]):
            logger.error(f"Email service not configured. Cannot send to {email}")
            raise Exception("Email service configuration incomplete")

        def send_sync():
            try:
                msg = MIMEMultipart()
                msg["From"] = f"{sender_name} <{sender_email}>"
                msg["To"] = email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain", "utf-8"))

                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
                server.quit()
                return True
            except Exception as e:
                logger.error(f"Error in sync SMTP send: {e}")
                raise

        success = await asyncio.to_thread(send_sync)
        logger.info(f"Password reset email sent successfully to {email}")

