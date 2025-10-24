from datetime import date, datetime
from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import List, Optional
import enum

class OrderStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"

class OrderSchema(BaseModel):
    id: str
    user_id: int
    package: str
    amount: int
    total_money: int
    description: str
    status: OrderStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OrderSchemaResponse(OrderSchema):
    username: str | None = None

    model_config = ConfigDict(from_attributes=True)

class user(BaseModel):
    id: int | None = None
    username: str | None = None
    role: str | None = None
    company_name: str | None = None
    coin: int | None = None
    avatar_path: str | None = None
    premium_expires: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)

class Service(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: int

    model_config = ConfigDict(from_attributes=True)