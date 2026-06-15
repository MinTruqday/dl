import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from core.config import settings
from loguru import logger

class EmailService:

    @staticmethod
    async def send_reset_password_email(email: str, token: str):
        smtp_host = settings.SMTP_HOST
        smtp_port = int(settings.SMTP_PORT) if settings.SMTP_PORT else None
        smtp_user = settings.SMTP_USER
        smtp_pass = settings.SMTP_PASS
        sender_email = settings.SENDER_EMAIL
        sender_name = settings.SENDER_NAME
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .container {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; background-color: #f9f9f9; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .header h2 {{ color: #333333; }}
                .content {{ background-color: #ffffff; padding: 20px; border-radius: 6px; color: #555555; line-height: 1.6; }}
                .token-container {{ text-align: center; margin: 20px 0; }}
                .token {{ display: inline-block; font-size: 28px; font-weight: bold; letter-spacing: 6px; padding: 12px 24px; background-color: #e3f2fd; color: #1976d2; border: 2px dashed #90caf9; border-radius: 6px; margin: 10px 0; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #999999; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header"><h2>Account Management System</h2></div>
                <div class="content">
                    <p>Hello,</p>
                    <p>We received a password recovery request for the account <strong>{email}</strong></p>
                    <p>Your verification code is</p>
                    <div class="token-container"><span class="token">{token}</span></div>
                    <p><strong>Note:</strong> This code is only valid for <strong>1 minute</strong></p>
                </div>
                <div class="footer"><p>This email was sent automatically please do not reply</p></div>
            </div>
        </body>
        </html>
        """

        logger.info(f"System initiating dispatch process for password recovery email to {email}")
        
        if not all([smtp_host, smtp_port, smtp_user, smtp_pass, sender_email, sender_name]):
            logger.error(f"Email dispatch process for {email} could not proceed due to incomplete configurations")
            raise Exception("Outbound mailing service is not properly configured to process this request")

        def send_sync():
            try:
                msg = MIMEMultipart()
                msg["From"] = f"{sender_name} <{sender_email}>"
                msg["To"] = email
                msg["Subject"] = "Password Recovery Verification Code"
                msg.attach(MIMEText(html_body, "html", "utf-8"))
                
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=settings.DEFAULT_HTTP_TIMEOUT)
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
                server.quit()
                return True
            except Exception:
                logger.error("Unexpected network or authentication error occurred communicating with outbound mail server")
                raise Exception("Unexpected network or authentication error occurred communicating with outbound mail server")

        await asyncio.to_thread(send_sync)
        logger.info(f"Password recovery instructions successfully transmitted to the provided email address {email}")