from graphene import (Schema, ObjectType)
from .user_schema import Query as UserQuery, Mutation as UserMutation
from .public_schema import Poem
from ..utilities import MongoengineCreateMutation, MongoengineUpdateMutation, MongoengineDeleteMutation
from ..roles import Role
from .. import schema_loader

"""
Query Objects
"""

class Query(UserQuery, ObjectType):
    pass

"""
Mutations
"""

class CreatePoem(MongoengineCreateMutation):
    class Meta:
        type = Poem

class UpdatePoem(MongoengineUpdateMutation):
    class Meta:
        type = Poem

class DeletePoem(MongoengineDeleteMutation):
    class Meta:
        type = Poem

class Mutation(UserMutation, ObjectType):
    create_poem = CreatePoem.Field()
    update_poem = UpdatePoem.Field()
    delete_poem = DeletePoem.Field()

"""
Schema
"""

schema = Schema(query=Query, mutation=Mutation)
schema_loader.use_for_role(Role.EDITOR, schema)