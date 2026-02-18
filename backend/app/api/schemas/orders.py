from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

from app.database.models import ErrandEvent, OrderStatus, TagName


class TagRead(BaseModel):
    name: TagName
    instruction: str


class BaseErrand(BaseModel):
    content: str
    weight: float = Field(le=150)
    destination: int


class ErrandCreate(BaseErrand):
    client_contact_email: EmailStr
    client_contact_phone: int | None = Field(default=None)


class ErrandUpdate(BaseModel):
    status: OrderStatus


class ErrandRead(BaseErrand):
    id: UUID
    timeline: list[ErrandEvent]
    estimated_delivery: datetime
    tags: list[TagRead]
