from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class ContactBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=3, max_length=50)
    date_of_birth: Optional[date] = None  # date
    information: Optional[str] = None
    # owner_id: int  # ID користувача-власника контакту


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=3, max_length=50)
    date_of_birth: Optional[date] = None
    information: Optional[str] = None


class ContactOut(ContactBase):
    id: int
    owner_id: int
    model_config = ConfigDict(from_attributes=True)


class ContactInDB(ContactBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserOut(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    avatar_url: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
