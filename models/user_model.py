from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from const.roles import Roles
import datetime
from enum import Enum


class UserTest(BaseModel):
    email: EmailStr
    fullName: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    passwordRepeat: str
    roles: List[Roles]

    banned: Optional[bool] = None
    verified: Optional[bool] = None


    @field_validator("email")
    @classmethod
    def check_email(cls, value: EmailStr) -> EmailStr:
        """
        Ментору - Вообще, я так понял, если у нас указан тип EmailStr для поля - текущий валидатор избыточен
        """
        if "@" not in value:
            raise ValueError("Email должен содерфжать символ @")
        return value

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        """
        Проверяем, что пароль содержит не меньше 8 символов.
        """
        if len(value) < 8:
            raise ValueError("Пароль должен быть не меньше 8 символов")
        return value


class RegisterUserResponse(BaseModel):
    id: str
    email: str = Field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", description="Email пользователя")
    fullName: str = Field(min_length=1, max_length=100, description="Полное имя пользователя")
    verified: bool
    banned: bool | None = None
    roles: List[Roles]
    createdAt: str = Field(description="Дата и время создания пользователя в формате ISO 8601")

    @classmethod
    @field_validator("createdAt")
    def validate_created_at(cls, value: str) -> str:
        # Валидатор для проверки формата даты и времени (ISO 8601).
        try:
            datetime.datetime.fromisoformat(value)
        except ValueError:
            raise ValueError("Некорректный формат даты и времени. Ожидается формат ISO 8601.")
        return value

class RegisteredUser(BaseModel):
    id: str
    email: EmailStr
    password: str


class CreateUserRequest(BaseModel):
    email: EmailStr
    fullName: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    roles: List[Roles]
    verified: bool = True
    banned: bool = False


class PatchUserRequest(BaseModel):
    roles: Optional[List[Roles]] = None
    verified: Optional[bool] = None
    banned: Optional[bool] = None


class PatchUserResponse(BaseModel):
    email: EmailStr
    fullName: str
    roles: List[Roles]
    verified: bool
    banned: bool
    createdAt: str


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

class GetAllUsersRequest(BaseModel):
    pageSize: int = Field(default=10, ge=1, le=100)
    page: int = Field(default=1, ge=1)
    roles: Optional[List[str]] = None
    createdAt: SortOrder = SortOrder.asc


class OneUserItem(BaseModel):
    """
    Это модель одного элемента в массиве users
    """
    id: str
    email: EmailStr
    fullName: str
    roles: List[Roles]
    verified: bool
    createdAt: str
    banned: bool


class GetAllUsersResponse(BaseModel):
    users: List[OneUserItem]
    count: int
    page: int
    pageSize: int