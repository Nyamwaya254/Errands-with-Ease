from fastapi import APIRouter

from app.routers import client, errands, delivery_partner, shared_auth

master_router = APIRouter()

master_router.include_router(client.router)
master_router.include_router(errands.router)
master_router.include_router(delivery_partner.router)
master_router.include_router(shared_auth.create_auth_router)
