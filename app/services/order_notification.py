"""Order event consumer – listens for order events and calls external API."""
import json

from aio_pika.abc import AbstractIncomingMessage
from loguru import logger

from app.clients.rest import get_rest_client


async def handle_order_event(message: AbstractIncomingMessage) -> None:
    """Process order events from RabbitMQ and send notifications."""
    body = json.loads(message.body)
    event = body.get("event")
    logger.info(f"Received order event: {event} | payload={body}")

    if event == "order.created":
        await _notify_order_created(body)
    else:
        logger.warning(f"Unknown order event: {event}")


async def _notify_order_created(payload: dict) -> None:
    """Call external notification API for new order creation."""
    client = await get_rest_client()
    notification_body = {
        "type": "order.created",
        "order_id": payload["order_id"],
        "user_id": payload["user_id"],
        "total_amount": payload["total_amount"],
        "items_count": len(payload.get("items", [])),
        "message": f"New order created: {payload['order_id']}",
    }
    try:
        resp = await client.post("/notifications", json=notification_body)
        logger.info(f"Order notification API response: {resp}")
    except Exception as exc:
        logger.error(f"Failed to call notification API for order: {exc}")
