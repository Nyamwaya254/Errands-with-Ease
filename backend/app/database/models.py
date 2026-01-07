from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from pydantic import EmailStr
from sqlmodel import Column, Field, Relationship, SQLModel
from sqlalchemy.dialects import postgresql


class OrderStatus(str, Enum):
    placed = "placed"
    in_transit = "in_transit"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    cancelled = "cancelled"


class TagName(str, Enum):
    FRAGILE = "fragile"
    PERISHABLE = "perishable"
    EXPRESS = "express"
    SIGNATURE_REQUIRED = "signature_required"
    PARCEL = "parcel"
    ELECTRONICS = "electronics"


class Orders(SQLModel, table=True):
    """Table for the orders placed"""

    __tablename__ = "orders"
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    shop_picked_at: str
    client_contact_email: EmailStr
    client_contact_phone: str | None
    destination: int
    content: str
    weight: float = Field(le=150)
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    client_id: UUID = Field(foreign_key="client.id")
    client: "Client" = Relationship(
        back_populates="order",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    delivery_partner_id: UUID = Field(foreign_key="delivery_partner.id")
    partner: "DeliveryPartner" = Relationship(
        back_populates="order",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class User(SQLModel):
    name: str

    email: EmailStr
    email_verified: bool = Field(default=False)
    password_hash: str = Field(exclude=True)


class Client(User, table=True):
    """Table for the user reqesting for a service"""

    __tablename__ = "client"
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    address: str | None = Field(default=None)
    zip_code: int | None = Field(default=None)
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    order: list[Orders] = Relationship(
        back_populates="client",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class DeliveryPartner(User, table=True):
    """Table for the delivery partners delivery the orders"""

    __tablename__ = "delivery_partner"
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    max_handling_capacity: int
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    order: list[Orders] = Relationship(
        back_populates="partner",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
