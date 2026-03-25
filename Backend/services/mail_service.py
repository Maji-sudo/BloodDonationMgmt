import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from dotenv import load_dotenv

load_dotenv()

mail_conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("EMAIL_USER"),
    MAIL_PASSWORD = os.getenv("EMAIL_PASS"),
    MAIL_FROM = os.getenv("EMAIL_FROM"),
    MAIL_PORT = int(os.getenv("EMAIL_PORT", 587)),
    MAIL_SERVER = os.getenv("EMAIL_SERVER"),
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send_otp_mail(recipient: str, otp: str):
    print(f"📨 STARTING MAIL DISPATCH TO: {recipient}")
    try:
        message = MessageSchema(
            subject="Action Required: Smart Blood Bank OTP",
            recipients=[recipient],
            body=f"""
            <html>
                <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f7; padding: 40px; margin: 0;">
                    <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #e11d48;">
                        <div style="padding: 30px; text-align: center;">
                            <h2 style="color: #1e293b; margin-bottom: 10px;">Verify Your Identity</h2>
                            <p style="color: #64748b; font-size: 16px;">Use the code below to complete your verification.</p>
                            
                            <div style="margin: 30px 0; background-color: #f8fafc; padding: 20px; border-radius: 8px; border: 1px dashed #cbd5e1;">
                                <span style="font-size: 36px; font-weight: bold; color: #e11d48; letter-spacing: 12px;">{otp}</span>
                            </div>
                            
                            <p style="color: #94a3b8; font-size: 14px;">This code expires in 10 minutes.</p>
                        </div>
                    </div>
                </body>
            </html>
            """,
            subtype=MessageType.html
        )

        fm = FastMail(mail_conf)
        await fm.send_message(message)
        print(f"✅ Email sent successfully to {recipient}")
    except Exception as e:
        print(f"❌ CRITICAL MAIL ERROR: {str(e)}")
        # Log to a file if needed
        with open("mail_errors.log", "a") as f:
            from datetime import datetime
            f.write(f"{datetime.utcnow()} - Error sending to {recipient}: {str(e)}\n")
