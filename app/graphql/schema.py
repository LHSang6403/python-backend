"""
Strawberry schema assembly + GraphQL router.
"""
import strawberry
from strawberry.fastapi import GraphQLRouter

from app.graphql.context import get_graphql_context
from app.graphql.mutations import Mutation
from app.graphql.queries import Query

schema = strawberry.Schema(query=Query, mutation=Mutation)

graphql_router = GraphQLRouter(
    schema,
    context_getter=get_graphql_context,
    graphiql=True,   # GraphiQL IDE at /graphql
)
