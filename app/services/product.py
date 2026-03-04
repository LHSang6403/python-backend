"""Product CRUD service."""
import uuid

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.rabbitmq import RabbitMQPublisher
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

PRODUCT_EVENTS_QUEUE = "product.events"


async def create_product(
    db: AsyncSession,
    data: ProductCreate,
    user_id: uuid.UUID,
    publisher: RabbitMQPublisher,
) -> Product:
    product = Product(**data.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(product)
    await db.flush()
    await db.refresh(product)

    # Publish product.created event
    try:
        await publisher.declare_queue_and_publish(
            PRODUCT_EVENTS_QUEUE,
            {
                "event": "product.created",
                "product_id": str(product.id),
                "name": product.name,
                "price": str(product.price),
                "created_by": str(user_id),
            },
        )
        logger.info(f"Published product.created event for product_id={product.id}")
    except Exception as exc:
        logger.error(f"Failed to publish product.created event: {exc}")

    return product


async def get_product(db: AsyncSession, product_id: uuid.UUID) -> Product:
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


async def get_products(
    db: AsyncSession, skip: int = 0, limit: int = 20
) -> list[Product]:
    result = await db.execute(select(Product).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_product(
    db: AsyncSession, product_id: uuid.UUID, data: ProductUpdate, user_id: uuid.UUID
) -> Product:
    product = await get_product(db, product_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    product.updated_by = user_id
    await db.flush()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product_id: uuid.UUID) -> None:
    product = await get_product(db, product_id)
    await db.delete(product)
    await db.flush()
