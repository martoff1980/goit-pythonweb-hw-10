from sqlalchemy import Column, Integer, String, Date, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    information = Column(String, nullable=True)

    owner_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner = relationship("User", back_populates="contacts")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, index=True, nullable=False)
    full_name = Column(String(200), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    avatar_url = Column(String(512), nullable=True)
    verification_token = Column(
        String(255), nullable=True
    )  # token for email verification

    contacts = relationship(
        "Contact", back_populates="owner", cascade="all, delete-orphan"
    )
