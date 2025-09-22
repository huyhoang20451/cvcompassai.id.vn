# Chứa các models của dữ liệu giữa các API
from datetime import date, datetime
from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import Optional

class user(BaseModel):
    id: int | None = None
    username: str | None = None
    role: str | None = None
    company_name: str | None = None
    coin: int | None = None
    model_config = ConfigDict(from_attributes=True)
    avatar_path: str | None = None