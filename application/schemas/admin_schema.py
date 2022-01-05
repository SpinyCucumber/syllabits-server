from graphene import (Schema, ObjectType)
from .user_schema import Query as UserQuery, Mutation as UserMutation
from .public_schema import Poem
from ..utilities import MongoengineCreateMutation

"""
Mutations
"""

class CreatePoem(MongoengineCreateMutation):
    class Meta:
        type = Poem

class Mutation(UserMutation, ObjectType):
    create_poem = CreatePoem.Field()

"""
Schema
"""

schema = Schema(query=UserQuery, mutation=UserMutation)