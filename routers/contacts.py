from fastapi import APIRouter, Query, Depends, HTTPException, status, Request, Form
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.deps import get_dep_current_user
from routers.users import get_current_user
from schemas import ContactCreate
from typing import List
from fastapi.templating import Jinja2Templates
from models import Contact, User
from fastapi.responses import RedirectResponse
from config import settings
from datetime import datetime
import schemas, crud, models

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/contacts", tags=["contacts"])


# 🏠 Головна сторінка зі списком контактів
@router.get("/")
async def read_contacts(
    request: Request,
    q: str | None = Query(None, description="Пошук за іменем, прізвищем або email"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Отримуємо JWT з cookies
    token = request.cookies.get("access_token")
    # user_email = None
    user_id = None

    try:
        # Токен має формат "Bearer <jwt>", тому можливо застосувати token.split()[1]
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # user_email = payload.get("sub")
        user_id = int(payload.get("sub"))
    except JWTError:
        # Якщо токен невалідний — редірект на логін
        return RedirectResponse(url="/login", status_code=303)

    # Отримуємо користувача за ID, бо sub = user.id
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Шукаємо контакти, які належать саме цьому користувачу
    if q:
        contacts = await crud.search_contacts(db, q, user.id)
    else:
        contacts = await crud.list_contacts(db, user_id=user.id)

    # Повертаємо шаблон зі списком контактів
    return templates.TemplateResponse(
        "contacts.html",
        {
            "request": request,
            "user": current_user,
            "contacts": contacts,
            "query": q or "",
        },
    )


@router.get("/add")
async def add_contact_form(request: Request):
    return templates.TemplateResponse("add_contact.html", {"request": request})


# 📤 Обробка POST-запиту з форми
@router.post("/add", status_code=status.HTTP_201_CREATED)
async def create_contact(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    birthday: str = Form(...),
    information: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    dob = None
    if birthday:
        dob = datetime.strptime(birthday, "%Y-%m-%d").date()

    data = schemas.ContactCreate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        date_of_birth=dob,
        information=information,
        owner_id=current_user.id,
    )
    await crud.create_contact(db, data, owner_id=current_user.id)
    return RedirectResponse("/contacts", status_code=303)


# ✏️ Форма редагування
@router.get("/edit/{contact_id}")
async def edit_contact_form(
    request: Request, contact_id: int, db: AsyncSession = Depends(get_db)
):
    contact = await crud.get_contact(db, contact_id)
    if not contact:
        return RedirectResponse("/contacts", status_code=303)
    return templates.TemplateResponse(
        "edit_contact.html", {"request": request, "contact": contact}
    )


@router.post("/edit/{contact_id}")
async def update_contact(
    contact_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    date_of_birth: str = Form(...),
    information: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    dob = None
    if date_of_birth:
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()

    data = schemas.ContactCreate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        date_of_birth=dob,
        information=information,
    )
    await crud.update_contact(db, contact_id, data)
    return RedirectResponse("/contacts", status_code=303)


# 🎂 API: Дні народження на найближчі 7 днів
@router.get("/birthdays/upcoming")
async def birthdays_page(
    request: Request,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contacts = await crud.upcoming_birthdays(db, user_id=current_user.id)
    return templates.TemplateResponse(
        "birthdays.html", {"request": request, "contacts": contacts}
    )


# ❌ Видалення контакту
@router.get("/delete/{contact_id}")
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    await crud.delete_contact(db, contact_id)
    return RedirectResponse("/contacts", status_code=303)
