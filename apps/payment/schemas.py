from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field
import enum

class OrderStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"

class pricemap(str, enum.Enum):
    candidate_xu = 10000
    candidate_premium = 50000
    business_premium = 500000

class OrderSchema(BaseModel):
    id: str
    user_id: int
    package: str
    amount: int
    total_money: int
    description: str
    status: OrderStatus

    model_config = ConfigDict(from_attributes=True)