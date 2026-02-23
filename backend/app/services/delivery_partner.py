from typing import Sequence
from fastapi import HTTPException, status
from sqlmodel import select, col
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user import UserService
from app.database.models import DeliveryPartner, Location, Orders, ServicableLocation
from app.api.schemas.delivery_partner import DeliveryPartnerCreate


class DeliveryPartnerService(UserService[DeliveryPartner]):
    """Service layer for delivery partner bs logic inherits generic Userservice"""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(DeliveryPartner, session)

    async def add(self, partner_create: DeliveryPartnerCreate):
        """Registers a new delivery partner and assigns their servicable locations"""
        partner: DeliveryPartner = await self._add_user(
            partner_create.model_dump(exclude={"serviceable_zip_codes"}),
            "delivery_partner",
        )
        # loops through the codes the partner provides to see if they exist in Location table then creates new entry if it doesnt exist
        # to the location and servicablelocations tabless
        for zip_code in partner_create.serviceable_zip_codes:
            location = await self.session.get(Location, zip_code)
            partner.servicable_locations.append(
                location if location else Location(zip_code=zip_code)
            )
        return await self._update(partner)

    async def get_partner_by_zipcode(self, zip_code: int) -> Sequence[DeliveryPartner]:
        """Fetches all delivery partners that service a specific zipcode"""

        return (
            await self.session.scalars(
                select(DeliveryPartner)
                .join(
                    ServicableLocation,
                    col(DeliveryPartner.id) == col(ServicableLocation.partner_id),
                )
                .join(
                    Location,
                    col(ServicableLocation.location_id) == col(Location.zip_code),
                )
                .where(Location.zip_code == zip_code)
            )
        ).all()

    async def assign_errand(self, errand: Orders) -> DeliveryPartner:
        """
        Assign a errand to the best available delivery partner

        Selection criteria:
        1. Partner must service the destination zip code
        2. Partner must have available capacity
        3. Choose partner with most available capacity in that destination
        """

        eligible_partners = await self.get_partner_by_zipcode(errand.destination)

        for partner in eligible_partners:
            if partner.current_handling_capacity > 0:
                partner.order.append(errand)
                return partner
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="No delivery partner available at the moment.Try again Later",
        )

    async def update(self, partner: DeliveryPartner) -> DeliveryPartner:
        """Updates to an existing partner record(handling capacity)"""
        return await self._update(partner)

    async def token(self, email: str, password) -> str:
        """Authenticate a delivery partner and return a JWT access token"""
        return await self._generate_token(email, password)
