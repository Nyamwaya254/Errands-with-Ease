from pathlib import Path
from typing import Annotated
from fastapi import Depends, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from app.api.dependancies import (
    ClientDep,
    ClientServiceDep,
    get_client_access_token,
    get_client_service,
)
from app.routers.shared_auth import create_auth_router
from app.api.schemas.client import ClientCreate, ClientRead
from app.core.security import TokenData
from app.config import app_settings

APP_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = APP_DIR / "templates"

templates = Jinja2Templates(TEMPLATE_DIR)

router = create_auth_router(
    prefix="/client",
    tags=["Client"],
    service_dep=get_client_service,
    token_dep=get_client_access_token,
)


@router.post("/signup", response_model=ClientRead)
async def register_client(payload: ClientCreate, service: ClientServiceDep):
    """Register a new client account and send a verifcation email"""
    return await service.add(payload)


@router.post("/token", response_model=TokenData)
async def login_client(
    request_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: ClientServiceDep,
):
    """Authenticate a client and issue a JWT access token"""
    token = await service.token(request_form.username, request_form.password)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/reset_password_form", include_in_schema=False)
async def get_reset_password(request: Request, token: str):
    """Serve the HTML password reset form"""
    return templates.TemplateResponse(
        request=request,
        name="password/reset.html",
        context={
            "reset_url": f"http://{app_settings.APP_DOMAIN}{router.prefix}/reset_password?token={token}"
        },
    )


@router.post("/reset_password")
async def reset_password_with_form(
    request: Request,
    token: str,
    password: Annotated[str, Form()],
    service: ClientServiceDep,
):
    """Reset Client password and return a HTML response"""

    is_success = await service.reset_password(token, password)
    return templates.TemplateResponse(
        request=request,
        name="password/success.html" if is_success else "password/failed.html",
    )


@router.get("/me", response_model=ClientRead)
async def get_client_profile(client: ClientDep):
    """Retrieve the clients profile"""
    return client


@router.get("/errands", response_model=list[ClientRead])
async def get_client_errands(client: ClientDep):
    """Retrieve all the errands of the client"""
    return client.order
