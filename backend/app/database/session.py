from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.config import db_settings
from app.database.models import Orders, Client, DeliveryPartner  # noqa


# create a database engine to connect with engine

engine = create_async_engine(
    url=db_settings.POSTGRES_URL,
    echo=True,
)


async def create_db_tables():
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


# session to interact with database
async def get_session():
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
