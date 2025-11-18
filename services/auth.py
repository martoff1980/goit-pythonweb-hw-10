from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from config import settings
from fastapi import HTTPException, Request

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MAX_BCRYPT_LENGTH = 72


def get_password_hash(password: str):
    truncated = password[:MAX_BCRYPT_LENGTH]
    return pwd_context.hash(truncated)


def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str | int, expires_delta: timedelta | None = None):
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"sub": str(subject), "exp": expire}
    encoded = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded


def create_refresh_token(subject: str | int, expires_delta: timedelta | None = None):
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode = {"sub": str(subject), "exp": expire}
    encoded = jwt.encode(
        to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded


def decode_access_token(token: str):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def verify_token(token: str):
    try:
        payload = decode_access_token(token)
        return payload.get("sub")
    except jwt.JWTError:
        return None


def get_token_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token.replace("Bearer ", "")
