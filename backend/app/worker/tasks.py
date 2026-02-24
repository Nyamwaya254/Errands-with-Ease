import asyncio
from pathlib import Path
from celery import Celery  # type: ignore[import-untyped]
from pydantic import EmailStr
from twilio.rest import Client  # type: ignore[import-untyped]
from fastapi_mail import (
    ConnectionConfig,
    FastMail,
    MessageSchema,
    MessageType,
    NameEmail,
)

from app.config import notification_settings, db_settings


APP_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = APP_DIR / "templates"

# fastmail setup for sending emails
fast_mail = FastMail(
    ConnectionConfig(
        **notification_settings.model_dump(
            exclude={"TWILIO_SID", "TWILIO_AUTH_TOKEN", "TWILIO_NUMBER"}
        ),
        TEMPLATE_FOLDER=TEMPLATE_DIR,
    )
)

# twilio setup for sending sms
twilio_client = Client(
    notification_settings.TWILIO_AUTH_TOKEN,
    notification_settings.TWILIO_SID,
)

# create a celery app
app = Celery(
    "api_tasks",  # name of the celery app
    broker=db_settings.REDIS_URL(
        9
    ),  # redis is used as message broker which receives and queues tasks
    backend=db_settings.REDIS_URL(9),  # redis to also store task results
    broker_connection_retry_on_startup=True,  # celery to keep retrying incase redis is not ready yet on startup
)


@app.task(name="send_mail")
def send_mail(recipients: list[str], subject: str, body: str):
    """Celery task to send a plain text mail"""
    recipient_list = [
        NameEmail(name=str(email), email=str(email)) for email in recipients
    ]
    asyncio.run(
        fast_mail.send_message(
            MessageSchema(
                recipients=recipient_list,
                subject=subject,
                body=body,
                subtype=MessageType.plain,
            )
        )
    )
    return "Message Sent!"


@app.task(name="send_email_with_template")
def send_email_with_template(
    recipients: list[EmailStr],
    subject: str,
    context: dict,
    template_name: str,
):
    """Celery task to send an email rendered from Jinja2 template"""
    recipient_list = [
        NameEmail(name=str(email), email=str(email)) for email in recipients
    ]
    try:
        asyncio.run(
            fast_mail.send_message(
                message=MessageSchema(
                    recipients=recipient_list,
                    subject=subject,
                    template_body=context,
                    subtype=MessageType.html,
                ),
                template_name=template_name,
            )
        )
    except Exception as e:
        print(f"EMAIL ERROR: {type(e).__name__}: {e}")
        raise  # marks task as FAILED in Celery


@app.task(name="send_sms")
def send_sms(to: str, body: str):
    """Celery task to send sms via Twilio"""
    twilio_client.messages.create(
        from_=notification_settings.TWILIO_NUMBER,
        to=to,
        body=body,
    )


@app.task(name="add_log")
def add_log(log: str) -> None:
    """Celery task to append a log entry to a local log file."""
    with open("file.log", "a") as file:
        file.write(f"{log}\n")
