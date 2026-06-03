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
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .container {{
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    background-color: #f9f9f9;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .header h2 {{
                    color: #333333;
                }}
                .content {{
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 6px;
                    color: #555555;
                    line-height: 1.6;
                }}
                .token-container {{
                    text-align: center;
                    margin: 20px 0;
                }}
                .token {{
                    display: inline-block;
                    font-size: 28px;
                    font-weight: bold;
                    letter-spacing: 6px;
                    padding: 12px 24px;
                    background-color: #e3f2fd;
                    color: #1976d2;
                    border: 2px dashed #90caf9;
                    border-radius: 6px;
                    margin: 10px 0;
                }}
                .footer {{
                    margin-top: 20px;
                    font-size: 12px;
                    color: #999999;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>DocLib</h2>
                </div>
                <div class="content">
                    <p>Chào bạn,</p>
                    <p>Chúng tôi nhận được yêu cầu khôi phục mật khẩu cho tài khoản <strong>{email}</strong>.</p>
                    <p>Mã xác thực của bạn là:</p>
                    <div class="token-container">
                        <span class="token">{token}</span>
                    </div>
                    <p><strong>Lưu ý:</strong> Mã này chỉ có hiệu lực trong vòng <strong>1 phút</strong>. Nếu bạn không yêu cầu thay đổi này, vui lòng bỏ qua email này.</p>
                    <p>Trân trọng,<br>Đội ngũ DocLib.</p>
                </div>
                <div class="footer">
                    <p>Email này được gửi tự động. Vui lòng không trả lời email này.</p>
                </div>
            </div>
        </body>
        </html>
        """

        logger.info(f"Reset token for {email}: {token}")

        if not all([smtp_host, smtp_port, smtp_user, smtp_pass, sender_email, sender_name]):
            logger.error(f"Email service not configured. Cannot send to {email}")
            raise Exception("Email service configuration incomplete")

        def send_sync():
            try:
                msg = MIMEMultipart()
                msg["From"] = f"{sender_name} <{sender_email}>"
                msg["To"] = email
                msg["Subject"] = subject
                msg.attach(MIMEText(html_body, "html", "utf-8"))

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

