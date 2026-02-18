from pydantic import BaseModel
from typing import Optional


class SettingOut(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    value: Optional[str] = None
