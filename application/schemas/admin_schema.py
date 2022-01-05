from graphene import (Schema, ObjectType)
from .user_schema import Query as UserQuery, Mutation as UserMutation
from .public_schema import Poem
from ..utilities import CreateMutation

"""
Mutations
"""

class CreatePoem(CreateMutation):
    class Meta:
        type = int

class Mutation(UserMutation, ObjectType):
    create_poem = CreatePoem.Field()

"""
Schema
"""

schema = Schema(query=UserQuery, mutation=UserMutation)