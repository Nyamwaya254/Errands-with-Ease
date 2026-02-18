from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generic, TypeVar

from sqlmodel import SQLModel
from uuid import UUID

ModelType = TypeVar("ModelType", bound=SQLModel)

"""Base service that any service can inherit from"""


class BaseService(
    Generic[ModelType]
):  # make BaseService Generic to avoid initiliazing on child services
    """Initialize the baseservice with a SQLModel class and an async db session"""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    """Retrieve a single record from db using its primary key"""

    async def _get(self, id: UUID):
        return await self.session.get(self.model, id)

    """Insert a new entity to db and return refreshed instance """

    async def _add(self, entity: SQLModel):
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    """Update an existing entity in db"""

    async def _update(self, entity: SQLModel):
        return await self._add(entity)

    """Delete an existing entity in db"""

    async def _delete(self, entity: SQLModel):
        await self.session.delete(entity)
