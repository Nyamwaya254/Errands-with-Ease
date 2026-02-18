from fastapi import APIRouter

from app.routers import client, errands, delivery_partner

master_router = APIRouter()

master_router.include_router(client.router)
master_router.include_router(errands.router)
master_router.include_router(delivery_partner.router)
