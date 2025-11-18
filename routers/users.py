from fastapi import (
    APIRouter,
    Request,
    Depends,
    HTTPException,
    status,
    Cookie,
    UploadFile,
    File,
)
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth import get_token_from_cookie
from database import get_db
from models import User
from config import settings
from jose import jwt, JWTError
from middleware.rate_limit import limiter
import crud
import cloudinary.uploader
import redis
import redis.asyncio as aioredis
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

RATE_LIMIT = 5  # requests
RATE_WINDOW = 60  # seconds

router = APIRouter(prefix="/users", tags=["users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# create redis connection pool
redis = None


async def get_redis():
    global redis
    if redis is None:
        redis = await aioredis.from_url(settings.REDIS_URL)
    return redis


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(get_token_from_cookie),  # Bearer из Authorization
    access_token: str = Cookie(None),  # Cookie
):
    actual_token = token or access_token

    if actual_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    try:
        payload = jwt.decode(
            actual_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: int = int(payload.get("sub"))

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = await db.get(User, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.get("/me")
@limiter.limit(f"{RATE_LIMIT}/{RATE_WINDOW}seconds")
async def get_me(request: Request, current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
    }


# в users router
@router.post("/avatar", status_code=201)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contents = await file.read()
    res = cloudinary.uploader.upload(
        contents, folder="avatars", public_id=f"user_{current_user.id}", overwrite=True
    )
    url = res.get("secure_url")
    await crud.update_avatar(db, current_user, url)
    return {"avatar_url": url}
