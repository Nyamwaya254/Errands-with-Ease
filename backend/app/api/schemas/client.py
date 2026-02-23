from pydantic import BaseModel, EmailStr, Field


class BaseClient(BaseModel):
    name: str
    email: EmailStr


class ClientCreate(BaseClient):
    password: str = Field(max_length=72)


class ClientRead(BaseClient):
    pass
