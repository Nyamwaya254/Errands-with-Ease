from uuid import UUID
from redis.asyncio import Redis

from app.config import db_settings


_token_blacklist = Redis(host=db_settings.REDIS_HOST, port=db_settings.REDIS_PORT, db=0)

_errand_verification_codes = Redis(
    host=db_settings.REDIS_HOST,
    port=db_settings.REDIS_PORT,
    db=1,
    decode_responses=True,
)


async def add_jti_to_blacklist(jti: str):
    """Adds a JWT token's unique identifier(JTI) to Redis blacklist"""
    await _token_blacklist.set(jti, "blacklisted")


async def is_jti_blacklisted(jti: str) -> bool:
    """Check whether jti exists in Redis blacklist"""
    return await _token_blacklist.exists(jti)


async def add_errand_verification_code(id: UUID, code: int):
    """Stores a 6 digit code for an errand in Redis"""
    await _errand_verification_codes.set(str(id), code)


async def get_errand_verification_code(id: UUID) -> str:
    """Retrieves the stored code for a given shipment"""
    return await _errand_verification_codes.get(str(id))
