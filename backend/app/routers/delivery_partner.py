from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.dependancies import (
    DeliveryPartnerDep,
    DeliveryPartnerServiceDep,
    get_delivery_partner_service,
    get_partner_access_token,
)
from app.routers.shared_auth import create_auth_router
from app.api.schemas.delivery_partner import (
    DeliveryPartnerCreate,
    DeliveryPartnerRead,
    DeliveryPartnerUpdate,
)
from app.core.security import TokenData

router = create_auth_router(
    prefix="/partner",
    tags=["Delivery Partner"],
    service_dep=get_delivery_partner_service,
    token_dep=get_partner_access_token,
)


@router.post("/signup", response_model=DeliveryPartnerRead)
async def register_delivery_partner(
    payload: DeliveryPartnerCreate,
    service: DeliveryPartnerServiceDep,
):
    """Register a new delivery partner and sends verification email"""
    return await service.add(payload)


@router.post("/token", response_model=TokenData)
async def login_delivery_partner(
    request_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: DeliveryPartnerServiceDep,
):
    """Authenticate a partner and issue a JWT access token
    Uses OAuth2 password flow- accepts username(email) and password from a form body
    """
    token = await service.token(request_form.username, request_form.password)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/update", response_model=DeliveryPartnerRead)
async def update_delivery_partner(
    payload: DeliveryPartnerUpdate,
    partner: DeliveryPartnerDep,
    service: DeliveryPartnerServiceDep,
):
    """Updates the authenticated delivery partner's profile"""
    update = payload.model_dump(exclude_none=True)
    if not update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided to update"
        )
    return await service.update(partner.sqlmodel_update(update))


@router.get("/me", response_model=DeliveryPartnerRead)
async def get_partner_profile(partner: DeliveryPartnerDep):
    """Retrieve the partners profile"""
    return partner


@router.get("/errands", response_model=list[DeliveryPartnerRead])
async def get_partner_errands(partner: DeliveryPartnerDep):
    """Retrieve all the errands of the partner"""
    return partner.order
