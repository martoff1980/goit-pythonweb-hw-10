from config import settings
from email.message import EmailMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Contact, User
import smtplib


# helper to send verification email (simple SMTP)
def send_verification_email(to_email: str, token: str):
    verify_link = f"http://localhost:8011/auth/verify?token={token}"
    msg = EmailMessage()
    msg["Subject"] = "Verify your account"
    msg["From"] = "no-reply@example.com"
    msg["To"] = to_email
    msg.set_content(f"Click to verify: {verify_link}")
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.send_message(msg)


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()
