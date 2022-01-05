from graphene import (Schema, ObjectType)
from .user_schema import Query as UserQuery, Mutation as UserMutation
from ..utilities import CreateMutation
from ..models import Poem as PoemModel

"""
Mutations
"""

class CreatePoem(CreateMutation):
    class Meta:
        model = PoemModel

class Mutation(UserMutation, ObjectType):
    create_poem = CreatePoem.Field()

"""
Schema
"""

schema = Schema(query=UserQuery, mutation=UserMutation)