from pydantic import BaseModel, EmailStr, Field


class BaseClient(BaseModel):
    name: str
    email: EmailStr


class ClientCreate(BaseClient):
    password: str = Field(max_length=72)
    address: str | None = Field(default=None)
    zip_code: int | None = Field(default=None)


class ClientRead(BaseClient):
    address: str | None = Field(default=None)
    zip_code: int | None = Field(default=None)
