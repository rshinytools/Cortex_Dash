# ABOUTME: Token models for authentication - JWT tokens and password reset
# ABOUTME: Used by the FastAPI template authentication system

from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None


class NewPassword(BaseModel):
    token: str
    new_password: str