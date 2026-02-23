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
    shop_picked_at: str | None = Field(default=None)


class ErrandCreate(BaseErrand):
    client_contact_email: EmailStr
    client_contact_phone: int | None = Field(default=None)


class ErrandUpdate(BaseModel):
    location: int | None = Field(default=None)
    status: OrderStatus | None = Field(default=None)
    verification_code: str | None = Field(default=None)
    description: str | None = Field(default=None)
    estimated_delivery: datetime | None = Field(default=None)


class ErrandRead(BaseErrand):
    id: UUID
    timeline: list[ErrandEvent]
    estimated_delivery: datetime
    tags: list[TagRead]
