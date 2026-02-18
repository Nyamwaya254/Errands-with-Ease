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

"""Adds a JWT token's unique identifier(JTI) to Redis blacklist"""


async def add_jti_to_blacklist(jti: str):
    await _token_blacklist.set(jti, "blacklisted")


"""Check whether jti exists in Redis blacklist"""


async def is_jti_blacklisted(jti: str) -> bool:
    return await _token_blacklist.exists(jti)


"""Stores a 6 digit code for an errand in Redis"""


async def add_errand_verification_code(id: UUID, code: int):
    await _errand_verification_codes.set(str(id), code)


"""Retrieves the stored code for a given shipment"""


async def get_errand_verification_code(id: UUID) -> str:
    return await _errand_verification_codes.get(str(id))
