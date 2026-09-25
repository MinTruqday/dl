import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from pathlib import Path

from loguru import logger

from src.core.infrastructure.configuration import settings

TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "templates"


def smtp_configuration():
    values = (
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        settings.SMTP_USER,
        settings.SMTP_PASS,
        settings.SENDER_EMAIL,
        settings.SENDER_NAME,
    )
    if not all(values):
        raise RuntimeError("Dịch vụ gửi thư điện tử chưa được cấu hình")
    return values


def dispatch(message):
    host, port, user, password, _, _ = smtp_configuration()
    with smtplib.SMTP(host, port, timeout=settings.SMTP_TIMEOUT_SECONDS) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(message)
    return True


def reset_password_body(email: str, token: str):
    template = (TEMPLATE_ROOT / "password_reset.html").read_text(encoding="utf-8")
    return (
        template.replace("{{email}}", escape(email))
        .replace("{{token}}", escape(token))
        .replace(
            "{{expiry_minutes}}",
            str(settings.PASSWORD_RESET_EXPIRE_MINUTES),
        )
    )


class EmailService:
    @staticmethod
    async def send_platform_test_email(email: str):
        smtp_configuration()
        message = MIMEText("Kiểm tra kết nối thư điện tử Veriq", "plain", "utf-8")
        message["From"] = f"{settings.SENDER_NAME} <{settings.SENDER_EMAIL}>"
        message["To"] = email
        message["Subject"] = "Kiểm tra kết nối Veriq"
        return await asyncio.to_thread(dispatch, message)

    @staticmethod
    async def send_reset_password_email(email: str, token: str):
        smtp_configuration()
        message = MIMEMultipart()
        message["From"] = f"{settings.SENDER_NAME} <{settings.SENDER_EMAIL}>"
        message["To"] = email
        message["Subject"] = "Mã xác thực khôi phục mật khẩu"
        message.attach(MIMEText(reset_password_body(email, token), "html", "utf-8"))
        try:
            await asyncio.to_thread(dispatch, message)
        except Exception as error:
            logger.exception("Password recovery email dispatch failed")
            raise RuntimeError(
                "Quá trình thiết lập kết nối đến máy chủ thư điện tử gặp sự cố"
            ) from error
        logger.info("Password recovery email notification dispatched")

    @staticmethod
    async def send_email_verification(email: str, token: str):
        smtp_configuration()
        message = MIMEText(
            f"Mã xác minh địa chỉ thư điện tử của bạn là {token}", "plain", "utf-8"
        )
        message["From"] = f"{settings.SENDER_NAME} <{settings.SENDER_EMAIL}>"
        message["To"] = email
        message["Subject"] = "Xác minh địa chỉ thư điện tử Veriq"
        return await asyncio.to_thread(dispatch, message)
