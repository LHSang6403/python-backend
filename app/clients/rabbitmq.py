"""
RabbitMQ async client – aio-pika robust connection with publisher & consumer.

Usage (FastAPI DI):
    from app.clients.rabbitmq import get_publisher, get_consumer

    async def endpoint(pub: RabbitMQPublisher = Depends(get_publisher)):
        await pub.publish(routing_key="my.queue", body={"event": "created"})
"""
import json
from collections.abc import Awaitable, Callable
from typing import Any

import aio_pika
from aio_pika import DeliveryMode, Message, connect_robust
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractIncomingMessage
from loguru import logger

from app.core.config import get_settings

settings = get_settings()

_connection: AbstractConnection | None = None
_channel: AbstractChannel | None = None


# ── Lifecycle ─────────────────────────────────────────────────────────────────

async def connect_rabbitmq() -> None:
    global _connection, _channel
    _connection = await connect_robust(settings.rabbitmq_url)
    _channel = await _connection.channel()
    await _channel.set_qos(prefetch_count=10)
    logger.info("RabbitMQ connected.")


async def disconnect_rabbitmq() -> None:
    global _connection, _channel
    if _channel and not _channel.is_closed:
        await _channel.close()
    if _connection and not _connection.is_closed:
        await _connection.close()
    _connection = None
    _channel = None
    logger.info("RabbitMQ disconnected.")


def _get_channel() -> AbstractChannel:
    if _channel is None:
        raise RuntimeError("RabbitMQ not initialised. Call connect_rabbitmq() first.")
    return _channel


# ── Publisher ─────────────────────────────────────────────────────────────────

class RabbitMQPublisher:
    """Publish JSON messages to an exchange or directly to a queue."""

    def __init__(self, channel: AbstractChannel) -> None:
        self._ch = channel

    async def publish(
        self,
        routing_key: str,
        body: Any,
        *,
        exchange_name: str = "",
        persistent: bool = True,
        headers: dict[str, Any] | None = None,
    ) -> None:
        exchange = await self._ch.get_exchange(exchange_name) if exchange_name \
            else await self._ch.get_exchange("")

        message = Message(
            body=json.dumps(body, default=str).encode(),
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT if persistent else DeliveryMode.NOT_PERSISTENT,
            headers=headers or {},
        )
        await exchange.publish(message, routing_key=routing_key)
        logger.debug(f"Published → routing_key={routing_key!r}")

    async def declare_queue_and_publish(
        self,
        queue_name: str,
        body: Any,
        *,
        persistent: bool = True,
    ) -> None:
        """Idempotently declare queue, then publish to it."""
        await self._ch.declare_queue(queue_name, durable=True)
        await self.publish(routing_key=queue_name, body=body, persistent=persistent)


# ── Consumer ──────────────────────────────────────────────────────────────────

MessageHandler = Callable[[AbstractIncomingMessage], Awaitable[None]]


class RabbitMQConsumer:
    """Subscribe to a queue and dispatch messages to a handler."""

    def __init__(self, channel: AbstractChannel) -> None:
        self._ch = channel

    async def consume(
        self,
        queue_name: str,
        handler: MessageHandler,
        *,
        durable: bool = True,
        auto_ack: bool = False,
    ) -> None:
        queue = await self._ch.declare_queue(queue_name, durable=durable)

        async def _wrapper(message: AbstractIncomingMessage) -> None:
            try:
                await handler(message)
                if not auto_ack:
                    await message.ack()
            except Exception as exc:
                logger.error(f"Error handling message from {queue_name!r}: {exc}")
                await message.nack(requeue=True)

        await queue.consume(_wrapper, no_ack=auto_ack)
        logger.info(f"Consuming from queue={queue_name!r}")


# ── FastAPI dependencies ───────────────────────────────────────────────────────

async def get_publisher() -> RabbitMQPublisher:
    return RabbitMQPublisher(_get_channel())


async def get_consumer() -> RabbitMQConsumer:
    return RabbitMQConsumer(_get_channel())
