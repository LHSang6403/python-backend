"""Notification consumer – listens for product events and calls external API."""
import json

from aio_pika.abc import AbstractIncomingMessage
from loguru import logger

from app.clients.rest import RestClient, get_rest_client


async def handle_product_event(message: AbstractIncomingMessage) -> None:
    """Process product events from RabbitMQ and send notifications."""
    body = json.loads(message.body)
    event = body.get("event")
    logger.info(f"Received event: {event} | payload={body}")

    if event == "product.created":
        await _notify_product_created(body)
    else:
        logger.warning(f"Unknown product event: {event}")


async def _notify_product_created(payload: dict) -> None:
    """Call external notification API for new product creation."""
    client = await get_rest_client()
    notification_body = {
        "type": "product.created",
        "product_id": payload["product_id"],
        "product_name": payload["name"],
        "price": payload["price"],
        "created_by": payload["created_by"],
        "message": f"New product created: {payload['name']}",
    }
    try:
        resp = await client.post("/notifications", json=notification_body)
        logger.info(f"Notification API response: {resp}")
    except Exception as exc:
        logger.error(f"Failed to call notification API: {exc}")
