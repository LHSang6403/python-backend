"""
Strawberry GraphQL – example Query.

Add your own @strawberry.field resolvers here.
Each resolver receives `info.context` (GraphQLContext) for DB/cache access.
"""
import strawberry
from strawberry.types import Info

from app.graphql.context import GraphQLContext


@strawberry.type
class Query:
    @strawberry.field(description="Health ping via GraphQL")
    async def ping(self, info: Info[GraphQLContext, None]) -> str:
        return "pong"
