from pydantic import BaseModel, EmailStr, Field


class BaseClient(BaseModel):
    name: str
    email: EmailStr


class ClentCreate(BaseClient):
    password: str = Field(max_length=72)


class SellerRead(BaseClient):
    pass
