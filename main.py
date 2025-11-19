from fastapi import (
    FastAPI,
    Request,
    BackgroundTasks,
    Form,
    Depends,
    Query,
    status,
    HTTPException,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from jose import JWTError, jwt
from database import get_db, engine
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from routers.contacts import router as contacts_router
from routers.users import get_current_user, router as user_router
from services.auth import (
    verify_password,
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from services.email import (
    get_user_by_email,
    send_verification_email,
    create_email_confirmation_token,
    router as email_router,
)
from middleware.auth import AuthMiddleware
from middleware.rate_limit import limiter
import models, crud, schemas

templates = Jinja2Templates(directory="templates")

app = FastAPI(title="Contacts API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔐 AUTH MIDDLEWARE
app.add_middleware(AuthMiddleware)
# підключаємо middleware та limiter
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(contacts_router)
app.include_router(user_router)
app.include_router(email_router)


# створити таблиці при старті (замість повноцінних міграцій)
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    token = request.cookies.get("access_token")

    if token:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            user_id = int(payload.get("sub"))

            return RedirectResponse("/contacts", status_code=303)

        except Exception:
            pass
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/register")
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_submit(
    request: Request,
    email: str = Form(...),
    full_name: str = Form(None),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = Depends(),
):
    try:
        # call auth.register logic - reuse crud and auth utils
        existing = await get_user_by_email(db, email)
        if existing:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "User exists"},
                status_code=409,
            )

        hashed = get_password_hash(password)
        user = models.User(
            email=email, full_name=full_name, hashed_password=hashed, is_verified=False
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Generate email confirmation token (JWT)
        token = create_email_confirmation_token(user.email)

        # Send email async in background
        background_tasks.add_task(send_verification_email, user.email, token)

        return RedirectResponse("/login?success=1", status_code=303)

    except Exception as e:
        await db.rollback()
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": f"Registration error: {str(e)}"},
            status_code=500,
        )


@app.get("/login")
async def login_form(request: Request):
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id = int(payload.get("sub"))
            return RedirectResponse("/contacts", status_code=303)
        except Exception:
            pass  # токен
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"},
            status_code=401,
        )

    token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    resp = RedirectResponse("/contacts", status_code=303)
    resp.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="None",
    )

    resp.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="None",
    )

    return resp


@app.post("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")

    # надійне видалення cookie
    resp.set_cookie(key="access_token", value="", expires=0, max_age=0)

    resp.set_cookie(key="refresh_token", value="", expires=0, max_age=0)

    return resp


@app.get("/profile")
async def profile(request: Request, current_user=Depends(get_current_user)):
    return templates.TemplateResponse(
        "profile.html", {"request": request, "user": current_user}
    )


@app.post("/auth/token")
async def login_token(
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(subject=user.id)

    response = JSONResponse({"access_token": token})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        secure=True,
        samesite="None",
    )
    return response


# Обробник помилки rate limit тільки для цього роутера
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(status_code=429, content={"error": "Too many requests"})
