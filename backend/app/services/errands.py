from datetime import datetime, timedelta
from fastapi import HTTPException, status
from uuid import UUID
from app.database.models import Client, DeliveryPartner, OrderStatus, Orders, TagName
from app.services.base import BaseService
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.delivery_partner import DeliveryPartnerService
from app.services.errand_event import ErrandEventService
from app.api.schemas.errands import ErrandCreate, ErrandUpdate
from app.database.redis import get_errand_verification_code


class ErrandService(BaseService[Orders]):
    """Service layer for all errands related bs logic"""

    def __init__(
        self,
        session: AsyncSession,
        partner_service: DeliveryPartnerService,  # used to find delivery partner and assign errand
        event_service: ErrandEventService,  # used to record timeline events when status changes
    ):
        """Initialize errandService with db session and dependent services"""
        super().__init__(Orders, session)
        self.partner_service = partner_service
        self.event_service = event_service

    async def get(self, id: UUID) -> Orders | None:
        """Fetches a single errand by id"""
        return await self._get(id)

    async def add(self, errand_create: ErrandCreate, client: Client) -> Orders:
        """Create a new errand,assign a delivery partner and record the initial event"""
        new_errand = Orders(
            **errand_create.model_dump(),
            status=OrderStatus.placed,
            estimated_delivery=datetime.now() + timedelta(days=3),
            client_id=client.id,
        )

        # find the best available partner for the destination zip code, raises 406 if partner is not available
        partner = await self.partner_service.assign_errand(new_errand)
        new_errand.delivery_partner_id = partner.id

        # add the errand in the db
        errand = await self._add(new_errand)

        # record the first timeline event so the errand has a status history from thr beginning
        event = await self.event_service.add(
            errand=errand,
            location=client.zip_code,
            status=OrderStatus.placed,
            description=f"Assigned to {partner.name}",
        )
        errand.timeline.append(event)
        return errand

    async def update(
        self,
        id: UUID,
        errand_update: ErrandUpdate,
        partner: DeliveryPartner,
    ) -> Orders:
        """Updates a errand status,estimated delivery with authorization checks(only assigned partner can update an errand)"""
        errand = await self.get(id)
        if errand is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Errand  not found"
            )
        if errand.delivery_partner_id != partner.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authorized to update errand",
            )
        if errand_update.status == OrderStatus.delivered:
            code = await get_errand_verification_code(errand.id)

            if code != errand_update.verification_code:
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail="Invalid verification code",
                )

        # remove none fields and verification code since its not a column
        update = errand_update.model_dump(
            exclude_none=True, exclude={"verification_code"}
        )

        if errand_update.estimated_delivery:
            errand.estimated_delivery = errand_update.estimated_delivery

        # Only record a timeline event if there's a status change or other updates
        # beyond just estimated_delivery, since estimated_delivery alone is not a status event
        if len(update) > 1 or not errand_update.estimated_delivery:
            await self.event_service.add(
                errand=errand,
                **update,
            )
        return await self._update(errand)

    async def cancel(self, id: UUID, client: Client) -> Orders:
        """Cancels a shipment and records the cancelled event on its timeline"""
        errand = await self.get(id)

        if errand is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Errand not found",
            )
        if errand.client_id != client.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not Authorized",
            )
        event = await self.event_service.add(
            errand=errand,
            status=OrderStatus.cancelled,
        )
        errand.timeline.append(event)

        return errand

    async def delete(self, id: UUID) -> None:
        """DEletes an errand from the database"""
        errand = await self.get(id)
        if errand is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Errand not found"
            )
        await self._delete(errand)

    async def add_tag(
        self, id: UUID, tag_name: TagName, instruction: str | None = None
    ) -> Orders:
        """Adds a tag to an errand ie fragile"""
        errand = await self.get(id)
        if errand is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Errand not found",
            )
        errand.tags.append(await tag_name.tag(self.session, instruction))
        return await self._update(errand)
