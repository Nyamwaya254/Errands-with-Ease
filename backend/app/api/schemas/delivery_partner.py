from pydantic import BaseModel, EmailStr, Field


class BaseDeliveryPartner(BaseModel):
    name: str
    email: EmailStr
    servicable_zip_codes: list[int] = []
    max_handling_capacity: int


class DeliveryPartnerCreate(BaseDeliveryPartner):
    password: str = Field(max_length=72)


class DeliveryPartnerRead(BaseDeliveryPartner):
    pass


class DeliveryPartnerUpdate(BaseModel):
    max_handling_capacity: int | None = Field(default=None)
