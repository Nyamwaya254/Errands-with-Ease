from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from pydantic import EmailStr
from sqlmodel import Column, Field, Relationship, SQLModel, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession


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

    async def tag(self, session: AsyncSession, instruction: str | None = None):
        tag = await session.scalar(select(Tag).where(Tag.name == self.value))
        if tag is None:
            tag = Tag(name=self.value, instruction=instruction)
            session.add(tag)
            await session.commit()
            await session.refresh(tag)
        return tag


class ErrandTag(SQLModel, table=True):
    __tablename__ = "shipment_tag"
    tag_id: UUID = Field(
        foreign_key="tag.id",
        primary_key=True,
    )

    shipment_id: UUID = Field(
        foreign_key="orders.id",
        primary_key=True,
    )


class Tag(SQLModel, table=True):
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    name: TagName
    instruction: str | None = Field(default=None)
    errands: list["Orders"] = Relationship(
        back_populates="tags",
        link_model=ErrandTag,
        sa_relationship_kwargs={"lazy": "immediate"},
    )


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
    estimated_delivery: datetime
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
    timeline: list["ErrandEvent"] = Relationship(
        back_populates="errands",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    tags: list[Tag] = Relationship(
        back_populates="errands",
        link_model=ErrandTag,
        sa_relationship_kwargs={"lazy": "immediate"},
    )

    @property
    def status(self):
        """Get the current status of the order."""
        return self.timeline[-1].status.value if len(self.timeline) > 0 else None


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


class ServicableLocation(SQLModel, table=True):
    __tablename__ = "servicable_location"

    partner_id: UUID = Field(
        foreign_key="delivery_partner.id",
        primary_key=True,
    )
    location_id: int = Field(
        foreign_key="location.zip_code",
        primary_key=True,
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
    servicable_locations: list["Location"] = Relationship(
        back_populates="delivery_partners",
        link_model=ServicableLocation,
        sa_relationship_kwargs={"lazy": "selectin"},
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

    @property
    def active_errands(self):
        """Get all orders that are currently in progress."""

        return [
            errand
            for errand in self.order
            if errand.status != OrderStatus.delivered
            and errand.status != OrderStatus.cancelled
        ]

    @property
    def current_handling_capacity(self):
        """Get the number of additional errands this partner can currently accept."""
        return self.max_handling_capacity - len(self.active_errands)


class Location(SQLModel, table=True):
    __tablename__ = "location"

    zip_code: int = Field(primary_key=True)

    # Additional metadata fields
    # estimated_delivery_days : int=Field(default=3)
    # surcharge: float = Field(default=0.0)
    # active: bool = Field(default=True)

    delivery_partners: list[DeliveryPartner] = Relationship(
        back_populates="servicable_locations",
        link_model=ServicableLocation,
        sa_relationship_kwargs={"lazy": "immediate"},
    )


class ErrandEvent(SQLModel, table=True):
    __tablename__ = "errand_event"

    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    location: int
    status: OrderStatus
    description: str | None = Field(default=None)
    errand_id: UUID = Field(foreign_key="orders.id")
    errands: Orders = Relationship(
        back_populates="timeline",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
