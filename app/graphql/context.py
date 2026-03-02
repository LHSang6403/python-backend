"""
GraphQL context – injects shared dependencies into resolvers.
"""
from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import BaseContext

from app.clients.postgres import get_db
from app.clients.redis import RedisCache, get_cache


@dataclass
class GraphQLContext(BaseContext):
    db: AsyncSession
    cache: RedisCache


async def get_graphql_context(
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache),
) -> GraphQLContext:
    return GraphQLContext(db=db, cache=cache)
