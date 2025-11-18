from fastapi import FastAPI, Request, Form, Depends, Query, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from jose import JWTError, jwt
from config import settings
from starlette.middleware.base import BaseHTTPMiddleware
from services.auth import create_access_token


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # path = request.url.path
        path = request.url.path.rstrip("/")

        # Маршрути без захисту
        public_paths = ["/", "/login", "/register", "/auth/token"]

        if any(path == pub or path.startswith(pub + "/") for pub in public_paths):
            return await call_next(request)

        # Отримання токенів з cookie
        access_token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")

        # 🔥 Якщо cookie видалени — НЕ авторизуємося!
        if not access_token and not refresh_token:
            return RedirectResponse("/login", status_code=303)

        # Перевірка access token
        if access_token:
            try:
                jwt.decode(
                    access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
                )
                return await call_next(request)
            except:
                pass

        # Перевірка refresh token
        if refresh_token:
            try:
                payload = jwt.decode(
                    refresh_token,
                    settings.REFRESH_SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                user_id = payload.get("sub")
                new_access = create_access_token(user_id)
                response = await call_next(request)
                response.set_cookie(
                    "access_token", new_access, httponly=True, samesite="lax"
                )
                return response
            except:
                return RedirectResponse("/login", status_code=303)

        return RedirectResponse("/login", status_code=303)
