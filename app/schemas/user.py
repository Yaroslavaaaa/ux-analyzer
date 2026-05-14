from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional
import uuid

# Базовые схемы
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    username: str
    email: EmailStr
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserInDB(UserResponse):
    id: uuid.UUID
    password_hash: str

# Токены
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None


class PasswordChange(BaseModel):
    """Схема для смены пароля"""
    old_password: str = Field(..., min_length=1, description="Текущий пароль")
    new_password: str = Field(..., min_length=6, description="Новый пароль (минимум 6 символов)")
    
    @validator('new_password')
    def password_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Password cannot be empty')
        return v

class PasswordChangeResponse(BaseModel):
    """Ответ после смены пароля"""
    message: str