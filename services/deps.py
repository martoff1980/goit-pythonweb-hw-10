from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import models
from services.auth import decode_access_token
from jose import JWTError
from sqlalchemy.future import select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_dep_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except (JWTError, Exception):
        raise credentials_exception
    stmt = select(models.User).where(models.User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user
