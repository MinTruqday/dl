import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger

class EmailService:
    @staticmethod
    async def send_reset_password_email(email: str, token: str):
        smtp_host = os.environ.get("SMTP_HOST")
        smtp_port = int(os.environ.get("SMTP_PORT"))
        smtp_user = os.environ.get("SMTP_USER")
        smtp_pass = os.environ.get("SMTP_PASS")
        sender_email = os.environ.get("SENDER_EMAIL")
        app_url = os.environ.get("URL")

        subject = "Mã xác thực khôi phục mật khẩu - DocLib"
        body = f"""Chào bạn,
Chúng tôi nhận được yêu cầu khôi phục mật khẩu cho tài khoản {email}.
Mã xác thực của bạn là: {token}
Lưu ý: Mã này chỉ có hiệu lực trong vòng 1 phút. Nếu bạn không yêu cầu thay đổi này, vui lòng bỏ qua email này.
Trân trọng,
Đội ngũ DocLib."""

        sender_name = os.environ.get("SENDER_NAME")

        if not all([smtp_host, smtp_user, smtp_pass]):
            logger.warning(f"SMTP not configured. Writing email content to logs/emails.log for {email}")
            os.makedirs("logs", exist_ok=True)
            with open("logs/emails.log", "a", encoding="utf-8") as f:
                f.write(f"--- {email} ---\nSubject: {subject}\nBody: {body}\n\n")
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = f"{sender_name} <{sender_email}>"
            msg["To"] = email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            logger.info(f"Password reset email sent successfully to {email}")
        except Exception as e:
            logger.error(f"Error sending email to {email}: {str(e)}")
            raise Exception("Hệ thống gửi email hiện đang bận, vui lòng thử lại sau.")
