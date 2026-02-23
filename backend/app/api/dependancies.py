from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from uuid import UUID

from app.database.session import get_session
from app.services.errands import ErrandService
from app.services.delivery_partner import DeliveryPartnerService
from app.services.errand_event import ErrandEventService
from app.services.client import ClientService
from app.utils import decode_access_token
from app.database.redis import is_jti_blacklisted
from app.core.security import oauth2_scheme_client, oauth2_scheme_partner
from app.database.models import Client, DeliveryPartner

# session dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_errand_service(session: SessionDep) -> ErrandService:
    """Injector dependency that returns a ErrandService instance"""
    return ErrandService(
        session,
        DeliveryPartnerService(session),
        ErrandEventService(session),
    )


# Errand service dependency annotation
ErrandServiceDep = Annotated[ErrandService, Depends(get_errand_service)]


def get_client_service(session: SessionDep) -> ClientService:
    """Injector dependency that returns a ClientService instance"""
    return ClientService(session)


# Client service dependency annotation
ClientServiceDep = Annotated[ClientService, Depends(get_client_service)]


def get_delivery_partner_service(session: SessionDep) -> DeliveryPartnerService:
    """Injector dependency that constructs a DeliveryPartnerService instance."""
    return DeliveryPartnerService(session)


# Delivery partner service dependency annotation
DeliveryPartnerServiceDep = Annotated[
    DeliveryPartnerService, Depends(get_delivery_partner_service)
]


async def _get_access_token(token: str) -> dict:
    """Decodes and validates a JWT access token."""
    data = decode_access_token(token)

    # validate data
    if data is None or await is_jti_blacklisted(data["jti"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token"
        )
    return data


# ----------Seller Authentication----------


async def get_client_access_token(
    token: Annotated[str, Depends(oauth2_scheme_client)],
) -> dict:
    """Extracts and validates the access token from the seller OAuth2 scheme."""
    return await _get_access_token(token)


async def get_current_client(
    token_data: Annotated[dict, Depends(get_client_access_token)], session: SessionDep
) -> Client:
    """Dependency that resolves the current auntenticated client from the database"""
    client = await session.get(Client, UUID(token_data["user"]["id"]))

    # if the account is deleted
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized"
        )
    return client


# logged in client dependency annotation
ClientDep = Annotated[Client, Depends(get_current_client)]


# --------Delivery Partner authentication-----


async def get_partner_access_token(
    token: Annotated[str, Depends(oauth2_scheme_partner)],
) -> dict:
    """Extracts and validates the access token from the delivery partner OAuth2 scheme."""
    return await _get_access_token(token)


async def get_current_partner(
    token_data: Annotated[dict, Depends(get_partner_access_token)], session: SessionDep
) -> DeliveryPartner:
    """Resolves the currently authenticated DeliveryPartner from the database."""
    partner = await session.get(DeliveryPartner, UUID(token_data["user"]["id"]))

    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized"
        )
    return partner


# logged in partner dependency annotation
DeliveryPartnerDep = Annotated[DeliveryPartner, Depends(get_current_partner)]
