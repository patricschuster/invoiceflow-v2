from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserOut(BaseModel):
    id: int
    username: str
    is_superuser: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str
    password: str
    is_superuser: bool = False
    is_active: bool = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    is_superuser: Optional[bool] = None
    is_active: Optional[bool] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
