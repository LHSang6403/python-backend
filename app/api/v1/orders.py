"""Order endpoints."""
import uuid

from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.clients.postgres import get_db
from app.clients.rabbitmq import RabbitMQPublisher, get_publisher
from app.clients.redis import get_redis
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order import create_order, get_order, get_orders

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order_endpoint(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    publisher: RabbitMQPublisher = Depends(get_publisher),
    current_user: User = Depends(get_current_user),
):
    return await create_order(db, data, current_user.id, redis, publisher)


@router.get("", response_model=list[OrderResponse])
async def list_orders_endpoint(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_orders(db, current_user.id, skip, limit)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_endpoint(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_order(db, order_id, current_user.id)
