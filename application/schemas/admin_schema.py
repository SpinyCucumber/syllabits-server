from graphene import (Schema, ObjectType)
from graphene_mongo import MongoengineConnectionField
from .editor_schema import Query as EditorQuery, Mutation as EditorMutation
from .user_schema import User
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

class Mutation(EditorMutation, ObjectType):
    pass

"""
Schema
"""

schema = Schema(query=Query, mutation=Mutation)
schema_loader.use_for_role(Role.ADMIN, schema)