from graphene import (Schema, ObjectType)
from .user_schema import Query as UserQuery, Mutation as UserMutation
from .public_schema import Poem
from ..utilities import MongoengineCreateMutation, MongoengineUpdateMutation

"""
Mutations
"""

class CreatePoem(MongoengineCreateMutation):
    class Meta:
        type = Poem

class UpdatePoem(MongoengineUpdateMutation):
    class Meta:
        type = Poem

class Mutation(UserMutation, ObjectType):
    create_poem = CreatePoem.Field()
    update_poem = UpdatePoem.Field()

"""
Schema
"""

schema = Schema(query=UserQuery, mutation=Mutation)