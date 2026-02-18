from uuid import uuid4
from fastapi import HTTPException, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
import jwt

from datetime import datetime, timedelta, timezone

from app.config import security_settings

# A single serializer instance used for all URL-safe token operations
# initialized once with the secret key so it's reused across all calls
_serializer = URLSafeTimedSerializer(security_settings.JWT_SECRET_KEY)

"""Generate a signed JWT access token."""


def generate_access_token(data: dict, expiry: timedelta = timedelta(days=3)) -> str:
    return jwt.encode(
        payload={**data, "jti": str(uuid4), "exp": datetime.now(timezone.utc) + expiry},
        algorithm=security_settings.JWT_ALGORITHM,
        key=security_settings.JWT_SECRET_KEY,
    )


"""Decode and verify a JWT access token."""


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            jwt=token,
            key=security_settings.JWT_SECRET_KEY,
            algorithms=[security_settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired Token"
        )
    except jwt.PyJWTError:
        return None


"""Generate a URL-safe signed token for use in verification links"""


def generate_url_safe_token(data: dict, salt: str | None = None) -> str:
    return _serializer.dumps(data, salt=salt)


"""    Decode and verify a URL-safe token"""


def decode_url_safe_token(
    token: str, salt: str | None = None, expiry: timedelta | None = None
) -> dict | None:
    try:
        return _serializer.loads(
            token,
            salt=salt,
            # convert timedelta to seconds since itsdangerous expects an integer
            max_age=int(expiry.total_seconds()) if expiry else None,
        )
    except (
        BadSignature,  # Token was valid but the expiry time has passed
        SignatureExpired,  # Token was tampered with or the salt doesn't match
    ):
        return None
