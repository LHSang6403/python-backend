"""Dashboard Endpoint - Ví dụ sức mạnh của asyncio"""
import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from sqlalchemy import select, func

# Import các config của source code bạn
from app.clients.postgres import get_db
from app.clients.redis import get_redis
from app.models.user import User
from app.models.order import Order

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    # ---------------------------------------------------------
    # BƯỚC 1: KHAI BÁO CÁC TÁC VỤ (CHƯA CHẠY, CHỈ MỚI ĐỊNH NGHĨA)
    # ---------------------------------------------------------
    
    # Task 1: Truy vấn CSDL Postgres đếm tổng số User
    async def count_users():
        result = await db.execute(select(func.count()).select_from(User))
        return result.scalar() or 0

    # Task 2: Truy vấn CSDL Postgres đếm tổng số Order
    async def count_orders():
        result = await db.execute(select(func.count()).select_from(Order))
        return result.scalar() or 0

    # Task 3: Chọc vào Redis để lấy số lượng giỏ hàng hoạt động
    async def get_active_carts():
        # Lấy số lượng keys bắt đầu bằng chữ "cart:" trong Redis
        keys = await redis.keys("cart:*")
        return len(keys)

    # ---------------------------------------------------------
    # BƯỚC 2: PHÁT ĐỘNG CHẠY SONG SONG TẤT CẢ TÁC VỤ
    # ---------------------------------------------------------
    
    print("⏳ Đang bắn 3 truy vấn đi cùng 1 lúc (Postgres x2, Redis x1)...")
    
    # asyncio.gather nhận các task và chạy đồng thời chúng.
    # Event loop sẽ không chờ task 1 xong mới qua task 2, mà tung cả 3 cùng lúc.
    total_users, total_orders, active_carts = await asyncio.gather(
        count_users(),
        count_orders(),
        get_active_carts()
    )

    # ---------------------------------------------------------
    # BƯỚC 3: TRẢ VỀ RESPONSES THEO ĐÚNG THỨ TỰ TRUYỀN VÀO GATHER
    # ---------------------------------------------------------
    print("✅ Cả 3 cơ sở dữ liệu đều đã phản hồi xong!")
    
    return {
        "status": "success",
        "data": {
            "users": total_users,
            "orders": total_orders,
            "active_carts": active_carts
        }
    }
