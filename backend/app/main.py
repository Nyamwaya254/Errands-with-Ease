from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware


from app.api.router import master_router


description = """
Errands Management System for Clients and delivery agents

###Seller
-Submit a errands effortless
-Share tracking links with customers

###Delivery Agent
-Track and Update Shipment Status
-Auto accept shipments
-Email and Sms notifications

###
Payment Intergration
"""


def custom_generate_unique_id_function(route: APIRoute) -> str:
    return route.name


app = FastAPI(
    title="Errands-With-Ease",
    description=description,
    version="0.1.0 ",
    terms_of_service="https://errandswithease.com/terms/",
    contact={
        "name": "Errands Support",
        "url": "https://errandswithease.com/support",
        "email": "suppport@errandswithease.com",
    },
    generate_unique_id_function=custom_generate_unique_id_function,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

app.include_router(master_router)
