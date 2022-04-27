from graphene import (Schema, ObjectType)
from graphene_mongo import MongoengineConnectionField
from .public_schema import Poem
from .editor_schema import Query as EditorQuery, Mutation as EditorMutation
from .user_schema import User
from ..utilities import MongoengineUpdateMutation, MongoengineDeleteMutation
from ..roles import Role
from .. import schema_loader

"""
Query Objects
"""

class Query(EditorQuery, ObjectType):
    # Administrators can view all users
    users = MongoengineConnectionField(User)

"""
Mutations
"""

# Administrators can update and delete users

class UpdateUser(MongoengineUpdateMutation):
    class Meta:
        type = User

class DeleteUser(MongoengineDeleteMutation):
    class Meta:
        type = User

class DeletePoem(MongoengineDeleteMutation):
    class Meta:
        type = Poem

class Mutation(EditorMutation, ObjectType):
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()
    delete_poem = DeletePoem.Field()

"""
Schema
"""

schema = Schema(query=Query, mutation=Mutation)
schema_loader.use_for_role(Role.ADMIN, schema)