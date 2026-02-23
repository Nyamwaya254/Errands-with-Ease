from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user import UserService
from app.database.models import Client
from app.api.schemas.client import ClientCreate


class ClientService(UserService[Client]):
    """Service for client-specific business logic inherits from the generic UserService"""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Client, session)

    async def add(self, client_create: ClientCreate) -> Client:
        """Register a new client in the database"""
        return await self._add_user(
            client_create.model_dump(),
            "client",
        )

    async def token(self, email, password) -> str:
        """Authenticate a client and return a JWT token"""
        return await self._generate_token(email, password)
