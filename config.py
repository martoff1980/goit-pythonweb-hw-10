from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    REDIS_URL: str = Field(..., env="REDIS_URL")

    SECRET_KEY: str = Field(..., env="SECRET_KEY")

    REFRESH_SECRET_KEY: str = Field(..., env=" REFRESH_SECRET_KEY")

    ALGORITHM: str = Field(..., env="ALGORITHM")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(..., env="ACCESS_TOKEN_EXPIRE_MINUTES")

    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(..., env="REFRESH_TOKEN_EXPIRE_DAYS")

    VERIFICATION_TOKEN_EXPIRE_HOURS: int = Field(
        ..., env=("VERIFICATION_TOKEN_EXPIRE_HOURS", 24)
    )

    SMTP_HOST: str = Field(..., env="SMTP_HOST")
    SMTP_PORT: int = Field(..., env="SMTP_PORT")
    SMTP_USER: int = Field(..., env="SMTP_USER")
    SMTP_PASS: int = Field(..., env="SMTP_PASS")
    SECRET_EMAIL: str = Field(..., env="SECRET_EMAIL")

    CLOUDINARY_CLOUD_NAME: str = Field(..., env="CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY: str = Field(..., env="CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET: str = Field(..., env="CLOUDINARY_API_SECRET")

    CORS_ORIGINS: str = Field(..., env="CORS_ORIGINS")

    class Config:
        env_file = ".env"


settings = Settings()
