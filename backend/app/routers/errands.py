from fastapi import APIRouter, HTTPException, Request, status
from uuid import UUID
from fastapi.templating import Jinja2Templates

from app.api.schemas.errands import ErrandCreate, ErrandRead, ErrandUpdate
from app.database.models import Orders, TagName
from app.api.dependancies import (
    DeliveryPartnerDep,
    ErrandServiceDep,
    SessionDep,
    ClientDep,
)
from backend.app.worker.tasks import TEMPLATE_DIR

router = APIRouter(prefix="/errand", tags=["Errands"])

templates = Jinja2Templates(TEMPLATE_DIR)


@router.get("/tag", response_model=ErrandRead)
async def add_tag_to_errand(id: UUID, tag_name: TagName, service: ErrandServiceDep):
    """Add a tag to an existing errand"""
    return await service.add_tag(id, tag_name)


@router.get("/tagged")
async def get_errands_with_tag(tag_name: TagName, session: SessionDep):
    """Retrieve all errands that have a specific tag applied"""
    tag = await tag_name.tag(session)
    return tag.errands


@router.post(
    "/",
    response_model=ErrandRead,
    name="Create Errand",
    description="Submit a new **Errand**",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "errand created"},
        status.HTTP_406_NOT_ACCEPTABLE: {
            "description": "Delivery Partner not available "
        },
    },
)
async def create_errand(
    payload: ErrandCreate, client: ClientDep, service: ErrandServiceDep
) -> Orders:
    """Create and submit a new errand"""
    return await service.add(payload, client)


@router.patch("/update", response_model=ErrandRead)
async def update_errand(
    id: UUID,
    payload: ErrandUpdate,
    partner: DeliveryPartnerDep,
    service: ErrandServiceDep,
):
    """Update an existing errand details"""
    update = payload.model_dump(exclude_none=True)
    if not update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided to update"
        )
    return await service.update(id, payload, partner)


@router.get("/", response_model=ErrandRead)
async def get_errand(id: UUID, service: ErrandServiceDep):
    """Retrieve a single errand by its uuid"""

    errand = await service.get(id)
    if errand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Given id does not exist"
        )
    return errand


@router.get("/cancel", response_model=ErrandRead)
async def cancel_errand(id: UUID, client: ClientDep, service: ErrandServiceDep):
    """Cancel an existing errand"""
    return await service.cancel(id, client)


@router.get("/track", include_in_schema=False)
async def get_tracking(request: Request, id: UUID, service: ErrandServiceDep):
    """Serves the HTML errand tracking page"""

    errand = await service.get(id)

    assert errand is not None
    context = errand.model_dump()
    context["status"] = errand.status
    context["partner"] = errand.partner.name
    context["timeline"] = errand.timeline
    context["timeline"].reverse()

    return templates.TemplateResponse(
        request=request,
        name="track.html",
        context=context,
    )
