"""
Strawberry GraphQL – example Mutation.

Add your own @strawberry.mutation resolvers here.
"""
import strawberry
from strawberry.types import Info

from app.graphql.context import GraphQLContext


@strawberry.type
class Mutation:
    @strawberry.mutation(description="Example mutation placeholder")
    async def noop(self, info: Info[GraphQLContext, None]) -> bool:
        return True
