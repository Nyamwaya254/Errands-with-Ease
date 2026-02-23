from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


oauth2_scheme_client = OAuth2PasswordBearer(
    tokenUrl="client/token",
    scheme_name="Client",
)
"""OAuth2 bearer scheme for client authentication.

Extracts the Bearer JWT token from the Authorization header on 
incoming requests to client-protected routes."""


oauth2_scheme_partner = OAuth2PasswordBearer(
    tokenUrl="partner/token",
    scheme_name="Delivery Partner",
)


class TokenData(BaseModel):
    """Response model returned to the client after successful authentication"""

    access_token: str
    token_type: str
