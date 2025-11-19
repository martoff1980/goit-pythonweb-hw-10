from fastapi import APIRouter, HTTPException, Depends
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jose import jwt
from config import settings
from email.message import EmailMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Contact, User
from database import get_db, engine
import smtplib
from datetime import datetime, timedelta


router = APIRouter(prefix="/auth", tags=["auth"])


conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASS,
    MAIL_FROM=settings.SMTP_USER,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_FROM_NAME="Contacts App",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)


# helper to send verification email (simple SMTP)
def send_verification_email(to_email: str, token: str):
    verify_link = f"http://localhost:8011/auth/confirm-email?token={token}"
    msg = EmailMessage()
    msg["Subject"] = "Verify your account"
    msg["From"] = "no-reply@example.com"
    msg["To"] = to_email
    msg.set_content(f"Click to verify: {verify_link}")
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.send_message(msg)


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()  # .scalar_one_or_none()


def create_email_confirmation_token(email: str):
    expire = datetime.utcnow() + timedelta(hours=24)
    payload = {"sub": email, "exp": expire}
    token = jwt.encode(payload, settings.SECRET_EMAIL, algorithm=settings.ALGORITHM)
    return token


def verify_email_token(token: str):
    try:
        payload = jwt.decode(
            token, settings.SECRET_EMAIL, algorithms=[settings.ALGORITHM]
        )
        return payload["sub"]
    except:
        return None


@router.get("/confirm-email")
async def confirm_email(token: str, db: AsyncSession = Depends(get_db)):
    email = verify_email_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    await db.commit()
    return {"message": "Email successfully confirmed"}
