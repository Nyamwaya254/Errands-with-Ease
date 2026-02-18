from random import randint
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.base import BaseService
from app.database.models import ErrandEvent, OrderStatus, Orders
from app.worker.tasks import send_email_with_template, send_sms
from app.utils import generate_url_safe_token
from app.config import app_settings
from app.database.redis import add_errand_verification_code

"""Service for managing shipment events"""


class ErrandEventService(BaseService):
    def __init__(self, session: AsyncSession):
        # Pass Errandevent as the model to BaseService so it knows  which table this service is responsible for
        super().__init__(ErrandEvent, session)

    """get the most recent event from shipment timeline"""

    async def get_latest_event(self, errand: Orders):
        timeline = errand.timeline
        # sort events oldest to newest by creation
        timeline.sort(key=lambda event: event.created_at)
        # return last item which the the most recent item
        return timeline[-1]

    """Add and persist a new shipment event"""

    async def add(
        self,
        errand: Orders,
        location: Optional[int] = None,
        status: Optional[OrderStatus] = None,
        description: Optional[str] = None,
    ) -> ErrandEvent:
        if location is None or status is None:
            if errand.timeline:
                # Get location/status from last event if timeline exists
                last_event = await self.get_latest_event(errand)
                if location is None:
                    location = last_event.location
                if status is None:
                    status = last_event.status
            else:
                # For first event, set defaults
                if location is None:
                    location = errand.destination
                if status is None:
                    status = OrderStatus.placed

        new_event = ErrandEvent(
            location=location,
            status=status,
            description=description
            if description
            else self._generate_description(
                status,
                location,
            ),
            errand_id=errand.id,
        )
        await self._notify(errand, status)

        return await self._add(new_event)

    def _generate_description(self, errand_status: OrderStatus, location: int):
        match errand_status:
            case OrderStatus.placed:
                return "Assigned delivery partner"
            case OrderStatus.out_for_delivery:
                return "Order is out for delivery"
            case OrderStatus.delivered:
                return "Successfuly delivered"
            case OrderStatus.cancelled:
                return "Order cancelled by the client"
            case _:  # and OrderStatus.in_transit
                return f"Scanned at {location}"

    async def _notify(self, errand: Orders, status: OrderStatus):
        if status == OrderStatus.in_transit:
            return

        match status:
            case OrderStatus.placed:
                send_email_with_template.delay(
                    recipients=[errand.client_contact_email],
                    subject="Your order is Shipped 🚛",
                    context={
                        "id": errand.id,
                        "client": errand.client.name,
                        "partner": errand.partner.name,
                    },
                    template_name="placed.html",
                )

            case OrderStatus.out_for_delivery:
                code = randint(100_000, 999_999)
                await add_errand_verification_code(errand.id, code)
                send_email_with_template.delay(
                    recipients=[errand.client_contact_email],
                    subject="Your order is out for delivery 🎯",
                    context={
                        "client": errand.client.name,
                        "partner": errand.partner.name,
                        "verification_code": code,
                    },
                    template_name="out_for_delivery.html",
                )

                if errand.client_contact_phone:
                    send_sms.delay(
                        to=errand.client_contact_phone,
                        body=f"YOur order is arriving soon! Share the {code} with the the delivery partner to receive your package",
                    )

            case OrderStatus.delivered:
                token = generate_url_safe_token({"id": str(errand.id)})
                send_email_with_template.delay(
                    recipients=[errand.client_contact_email],
                    subject="Your order has been delivered 📦✨",
                    context={
                        "client": errand.client.name,
                        "partner": errand.partner.name,
                        "review_url": f"http://{app_settings.APP_DOMAIN}/errand/review?token={token}",
                    },
                    template_name="delivered.html",
                )

            case OrderStatus.cancelled:
                send_email_with_template.delay(
                    recipients=[errand.client_contact_email],
                    subject="Your order has been cancelled ❌",
                    context={
                        "client": errand.client.name,
                        "partner": errand.partner.name,
                    },
                    template_name="cancelled.html",
                )
