"""Order service – create with pessimistic locking + Redis stock cache."""
import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.rabbitmq import RabbitMQPublisher
from app.core.config import get_settings
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate

settings = get_settings()

ORDER_EVENTS_QUEUE = "order.events"
STOCK_KEY_PREFIX = "stock:"


async def create_order(
    db: AsyncSession,
    data: OrderCreate,
    user_id: uuid.UUID,
    redis: Redis,
    publisher: RabbitMQPublisher,
) -> Order:
    product_quantities: dict[uuid.UUID, int] = {}
    for item in data.items:
        product_quantities[item.product_id] = (
            product_quantities.get(item.product_id, 0) + item.quantity
        )

    # 1. Quick Redis cache check (non-authoritative, fail-fast)
    for pid, qty in product_quantities.items():
        cached = await redis.get(f"{STOCK_KEY_PREFIX}{pid}")
        if cached is not None and int(cached) < qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {pid}",
            )

    # 2. Pessimistic lock – sorted by ID to prevent deadlocks
    sorted_pids = sorted(product_quantities.keys())
    result = await db.execute(
        select(Product)
        .where(Product.id.in_(sorted_pids))
        .with_for_update()
        .order_by(Product.id)
    )
    products: dict[uuid.UUID, Product] = {p.id: p for p in result.scalars().all()}

    # Validate all products exist
    missing = set(sorted_pids) - set(products.keys())
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Products not found: {[str(m) for m in missing]}",
        )

    # 3. Validate stock after acquiring lock
    for pid, qty in product_quantities.items():
        product = products[pid]
        if product.quantity < qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {product.name}",
            )

    # 4. Deduct stock, create Order + OrderItems
    total_amount = Decimal("0.00")
    order = Order(user_id=user_id, status=OrderStatus.pending, total_amount=Decimal("0.00"))
    db.add(order)
    await db.flush()

    order_items: list[OrderItem] = []
    for item in data.items:
        product = products[item.product_id]
        product.quantity -= item.quantity
        line_total = product.price * item.quantity
        total_amount += line_total

        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=product.price,
        )
        db.add(order_item)
        order_items.append(order_item)

    order.total_amount = total_amount
    await db.flush()

    # 5. Update Redis stock cache
    for pid, product in products.items():
        await redis.set(
            f"{STOCK_KEY_PREFIX}{pid}",
            str(product.quantity),
            ex=settings.stock_cache_ttl,
        )

    # 6. Publish order.created event
    try:
        await publisher.declare_queue_and_publish(
            ORDER_EVENTS_QUEUE,
            {
                "event": "order.created",
                "order_id": str(order.id),
                "user_id": str(user_id),
                "total_amount": str(total_amount),
                "items": [
                    {
                        "product_id": str(oi.product_id),
                        "quantity": oi.quantity,
                        "unit_price": str(oi.unit_price),
                    }
                    for oi in order_items
                ],
            },
        )
        logger.info(f"Published order.created event for order_id={order.id}")
    except Exception as exc:
        logger.error(f"Failed to publish order.created event: {exc}")

    await db.refresh(order)
    return order


async def get_orders(
    db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 20
) -> list[Order]:
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_order(
    db: AsyncSession, order_id: uuid.UUID, user_id: uuid.UUID
) -> Order:
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    if order.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order",
        )
    return order
