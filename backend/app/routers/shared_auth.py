from enum import Enum
from typing import Annotated, Awaitable, Callable, TypeVar
from fastapi import APIRouter, Depends
from app.services.user import UserService
from app.database.redis import add_jti_to_blacklist


T = TypeVar("T", bound=UserService)


def create_auth_router(
    prefix: str,
    tags: list[str | Enum] | None,
    service_dep: Callable[..., T],
    token_dep: Callable[..., Awaitable[dict]],
) -> APIRouter:
    """Factory function that builds an APIRouter with shared auth endpoints
    Accepts user-type-specific  dependencies and wires them into routes for authentication
    """
    router = APIRouter(prefix=prefix, tags=tags)

    @router.get("/verify")
    async def verify_user_email(
        token: str, service: Annotated[T, Depends(service_dep)]
    ):
        """Verify the user's email address using a signed token"""
        await service.verify_email(token)
        return {"detail": "Account verified"}

    @router.get("/forgot_password")
    async def forgot_password(email: str, service: Annotated[T, Depends(service_dep)]):
        """
        Generates a signed reset token and emails the link pointing to the reset_passwors endpoint
        """
        await service.send_password_reset_link(email, prefix)
        return {"detail": "Check your email to reset your password"}

    @router.post("/reset_password")
    async def reset_password(
        token: str, password: str, service: Annotated[T, Depends(service_dep)]
    ):
        """Validates the reset token then updates the account password with the one the user gave"""
        await service.reset_password(token, password)
        return {"detail": "Password reset successfully"}

    @router.post("/logout")
    async def logout(token_data: Annotated[dict, Depends(token_dep)]):
        """Log out authenticated user"""
        await add_jti_to_blacklist(token_data["jti"])
        return {"detail": "Successfully logged out"}

    return router
