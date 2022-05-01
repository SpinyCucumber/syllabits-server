from graphene import (Schema, ObjectType)
from graphene_mongo import MongoengineConnectionField
from .public_schema import Poem, Page
from .editor_schema import Query as EditorQuery, Mutation as EditorMutation
from .user_schema import User
from ..utilities import MongoengineUpdateMutation, MongoengineDeleteMutation, MongoengineCreateMutation
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

# Administrators can delete poems

class DeletePoem(MongoengineDeleteMutation):
    class Meta:
        type = Poem

# Administrators can create, update and delete pages

class CreatePage(MongoengineCreateMutation):
    class Meta:
        type = Page

class UpdatePage(MongoengineUpdateMutation):
    class Meta:
        type = Page

class DeletePage(MongoengineDeleteMutation):
    class Meta:
        type = Page

class Mutation(EditorMutation, ObjectType):
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()
    delete_poem = DeletePoem.Field()
    create_page = CreatePage.Field()
    update_page = UpdatePage.Field()
    delete_page = DeletePage.Field()

"""
Schema
"""

schema = Schema(query=Query, mutation=Mutation)
schema_loader.use_for_role(Role.ADMIN, schema)