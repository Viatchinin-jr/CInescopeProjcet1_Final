from pydantic import BaseModel, EmailStr
from const.roles import Roles
from typing import List, Optional




class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginUserInfo(BaseModel):
    id: str
    email: EmailStr
    roles: List[Roles]
    verified: bool | None = None
    banned: bool | None = None


class LoginResponse(BaseModel):
    user: LoginUserInfo
    accessToken: str
    expiresIn: int

class RefreshTokenResponse(BaseModel):
    accessToken: str
    expireIn: int | None = None


class LogoutResponse(BaseModel):
    message: Optional[str] = None