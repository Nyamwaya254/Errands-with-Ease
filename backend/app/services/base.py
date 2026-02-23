from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generic, TypeVar

from sqlmodel import SQLModel
from uuid import UUID

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseService(
    Generic[ModelType]
):  # make BaseService Generic to avoid initiliazing on child services
    """Base service that any service can inherit from"""

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        """Initialize the baseservice with a SQLModel class and an async db session"""
        self.model = model
        self.session = session

    async def _get(self, id: UUID):
        """Retrieve a single record from db using its primary key"""
        return await self.session.get(self.model, id)

    async def _add(self, entity: SQLModel):
        """Insert a new entity to db and return refreshed instance"""

        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def _update(self, entity: SQLModel):
        """Update an existing entity in db"""
        return await self._add(entity)

    async def _delete(self, entity: SQLModel):
        """Delete an existing entity in db"""
        await self.session.delete(entity)
