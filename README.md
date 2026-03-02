# python-backend

FastAPI backend scaffold với đầy đủ clients:
**PostgreSQL · Redis · RabbitMQ · REST API · GraphQL**

## Cấu trúc

```
python-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py     # Đăng ký routers
│   │       └── health.py       # Liveness & readiness endpoints
│   ├── clients/
│   │   ├── postgres.py         # SQLAlchemy async engine + session
│   │   ├── redis.py            # Redis pool + RedisCache wrapper
│   │   ├── rabbitmq.py         # RabbitMQ Publisher + Consumer
│   │   └── rest.py             # HTTPX client với retry/backoff
│   ├── core/
│   │   ├── config.py           # Settings (pydantic-settings, .env)
│   │   └── logging.py          # Loguru setup
│   ├── graphql/
│   │   ├── context.py          # GraphQL context (DB + Cache)
│   │   ├── queries.py          # Query resolvers
│   │   ├── mutations.py        # Mutation resolvers
│   │   └── schema.py           # Schema + GraphQLRouter
│   └── main.py                 # App factory + lifespan
├── migrations/
│   ├── env.py                  # Alembic async env
│   ├── script.py.mako
│   └── versions/
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Endpoints

| URL | Mô tả |
|-----|--------|
| `GET  /docs` | Swagger UI |
| `GET  /redoc` | ReDoc |
| `GET  /api/v1/health` | Liveness probe |
| `GET  /api/v1/health/ready` | Readiness probe (Postgres + Redis) |
| `GET/POST /graphql` | GraphQL endpoint + GraphiQL IDE |

## Cài đặt và chạy

### Local

```bash
# Tạo virtualenv
python -m venv .venv && source .venv/bin/activate

# Cài packages
pip install -r requirements.txt

# Copy env
cp .env.example .env

# Chạy server
uvicorn app.main:app --reload
```

### Docker

```bash
docker-compose up -d
```

## Migrations (Alembic)

```bash
# Tạo migration mới
alembic revision --autogenerate -m "create_table_xxx"

# Chạy migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Thêm domain mới

1. Tạo model trong `app/models/`
2. Tạo schema Pydantic trong `app/schemas/`
3. Tạo router trong `app/api/v1/your_domain.py`
4. Đăng ký router trong `app/api/v1/__init__.py`
5. (Tùy chọn) Thêm GraphQL types/queries/mutations trong `app/graphql/`