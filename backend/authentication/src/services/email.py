import asyncio
import os
import smtplib
from src.core.logic_logger import log_logic_execution
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from loguru import logger

from src.core.infrastructure.configuration import settings

class EmailService:

    @staticmethod
    @log_logic_execution
    async def send_reset_password_email(email: str, token: str):
        smtp_host = settings.SMTP_HOST
        smtp_port_raw = settings.SMTP_PORT
        smtp_port = int(smtp_port_raw) if smtp_port_raw else None
        smtp_user = settings.SMTP_USER
        smtp_pass = settings.SMTP_PASS
        sender_email = settings.SENDER_EMAIL
        sender_name = settings.SENDER_NAME
        subject = "Mã xác thực khôi phục mật khẩu"
        html_body = f'\n        <!DOCTYPE html>\n        <html>\n        <head>\n            <style>\n                .container {{\n                    font-family: Arial, sans-serif;\n                    max-width: 600px;\n                    margin: 0 auto;\n                    padding: 20px;\n                    border: 1px solid #e0e0e0;\n                    border-radius: 8px;\n                    background-color: #f9f9f9;\n                }}\n                .header {{\n                    text-align: center;\n                    margin-bottom: 20px;\n                }}\n                .header h2 {{\n                    color: #333333;\n                }}\n                .content {{\n                    background-color: #ffffff;\n                    padding: 20px;\n                    border-radius: 6px;\n                    color: #555555;\n                    line-height: 1.6;\n                }}\n                .token-container {{\n                    text-align: center;\n                    margin: 20px 0;\n                }}\n                .token {{\n                    display: inline-block;\n                    font-size: 28px;\n                    font-weight: bold;\n                    letter-spacing: 6px;\n                    padding: 12px 24px;\n                    background-color: #e3f2fd;\n                    color: #1976d2;\n                    border: 2px dashed #90caf9;\n                    border-radius: 6px;\n                    margin: 10px 0;\n                }}\n                .footer {{\n                    margin-top: 20px;\n                    font-size: 12px;\n                    color: #999999;\n                    text-align: center;\n                }}\n            </style>\n        </head>\n        <body>\n            <div class="container">\n                <div class="header">\n                    <h2>Hệ thống quản lý tài khoản</h2>\n                </div>\n                <div class="content">\n                    <p>Chào bạn</p>\n                    <p>Chúng tôi nhận được yêu cầu khôi phục mật khẩu cho tài khoản <strong>{email}</strong></p>\n                    <p>Mã xác thực của bạn là</p>\n                    <div class="token-container">\n                        <span class="token">{token}</span>\n                    </div>\n                    <p><strong>Lưu ý</strong> Mã này chỉ có hiệu lực trong vòng <strong>1 phút</strong> Nếu bạn không yêu cầu thay đổi này vui lòng bỏ qua email này</p>\n                    <p>Trân trọng</p>\n                </div>\n                <div class="footer">\n                    <p>Email này được gửi tự động vui lòng không trả lời email này</p>\n                </div>\n            </div>\n        </body>\n        </html>\n        '
        logger.info("Initiating dispatch process for password recovery email notification")
        if not all(
            [smtp_host, smtp_port, smtp_user, smtp_pass, sender_email, sender_name]
        ):
            logger.error("SMTP credentials are not properly configured")
            raise Exception("Dịch vụ gửi thư điện tử chưa được cấu hình hoặc cấu hình không chính xác")

        def send_sync():
            try:
                msg = MIMEMultipart()
                msg["From"] = f"{sender_name} <{sender_email}>"
                msg["To"] = email
                msg["Subject"] = subject
                msg.attach(MIMEText(html_body, "html", "utf-8"))
                server = smtplib.SMTP(
                    smtp_host, smtp_port, timeout=settings.DEFAULT_HTTP_TIMEOUT
                )
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
                server.quit()
                return True
            except Exception as e:
                logger.exception("Failed to establish connection with upstream SMTP server for email dispatch")
                raise Exception("Quá trình thiết lập kết nối đến máy chủ thư điện tử gặp sự cố")

        success = await asyncio.to_thread(send_sync)
        logger.info("Password recovery email notification dispatched successfully to upstream server")
