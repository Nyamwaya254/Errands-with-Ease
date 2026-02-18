from typing import TypeVar
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlmodel import select
from uuid import UUID
from datetime import timedelta

from app.services.base import BaseService
from app.database.models import User
from app.utils import (
    decode_url_safe_token,
    generate_access_token,
    generate_url_safe_token,
)
from app.worker.tasks import send_email_with_template
from app.config import app_settings

password_context = CryptContext(schemes=["argon2"], deprecated="auto")

ModelType = TypeVar(
    "ModelType", bound=User
)  # make UserService generic so as to initialize only once and avoid overriding


"""User service that can be inherited by client and delivery_partner"""


class UserService(BaseService[ModelType]):
    """Creates a new user, hashes their password, saves them to the database,
    and sends a verification email.
    """

    async def _add_user(self, data: dict, router_prefix: str):
        user = self.model(
            **data,
            password_hash=password_context.hash(data["password"]),
        )
        user = await self._add(user)

        token = generate_url_safe_token(
            {
                "email": user.email,
                "id": str(user.id),  # type: ignore[attr-defined]
            }
        )
        # send email to verify user with verification link
        send_email_with_template.delay(
            recipients=[user.email],
            subject="Verify your email with Errands With Ease",
            context={
                "username": user.name,
                "verification_url": f"http://{app_settings.APP_DOMAIN}/{router_prefix}/verify?token={token}",
            },
            template_name="email_verify.html",
        )
        return user

    """Look up a user in the database by their email address."""

    async def _get_by_email(self, email) -> User | None:
        return await self.session.scalar(
            select(self.model).where(self.model.email == email)
        )

    """Verifies a user's email address using a token sent to them during registration."""

    async def verify_email(self, token: str):
        token_data = decode_url_safe_token(token)

        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Token"
            )
        user = await self._get(UUID(token_data["id"]))
        user.email_verified = True
        await self._update(user)

    """Generates a password reset token and emails a reset link to the user."""

    async def send_password_reset_link(self, email, router_prefix):
        user = await self._get_by_email(email)

        token = generate_url_safe_token({"id": str(user.id)}, salt="password-reset")

        send_email_with_template.delay(
            recipients=[user.email],
            subject="Errands with Ease reset Password",
            context={
                "username": user.name,
                "reset_url": f"http://{app_settings.APP_DOMAIN}/{router_prefix}/reset_password_form?token={token}",
            },
            template_name="password_reset.html",
        )

    """Resets a user's password using a valid password reset token."""

    async def reset_password(self, token: str, password: str) -> bool:
        token_data = decode_url_safe_token(
            token, salt="password-reset", expiry=timedelta(days=1)
        )
        if not token_data:
            return False

        user = await self._get(UUID(token_data["id"]))

        user.password_hash = password_context.hash(password)
        await self._update(user)
        return True

    """Validates user credentials and generates a JWT access token for authentication."""

    async def _generate_token(self, email, password):
        # validate credentials
        user = await self._get_by_email(email)

        if user is None or not password_context.verify(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email or Password is incorrect",
            )
        if not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Email is not verified"
            )
        return generate_access_token(
            data={"user": {"name": user.name, "id": str(user.id)}}
        )
