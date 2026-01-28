from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.enum import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role: Optional[str] = UserRole.ARCHITECT.value


class UserResponse(UserBase):
    id: int
    role: str

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
