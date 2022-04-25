from graphene_mongo import MongoengineObjectType
from graphene import (Node, GlobalID, Schema, Mutation, ObjectType, InputObjectType, Boolean, Field, Enum)
from datetime import datetime
from flask_jwt_extended import get_jwt

from .public_schema import Query as PublicQuery, Mutation as PublicMutation
from ..models import Progress as ProgressModel, User as UserModel, TokenBlocklist as TokenBlocklistModel, Role as RoleModel
from .. import schema_loader

"""
Queries/Object Types
"""

Role = Enum.from_enum(RoleModel)

class User(MongoengineObjectType):
    class Meta:
        model = UserModel
        interfaces = (Node,)
        # Definitely don't want to expose this
        exclude_fields = ('password_hashed', 'role')
    role = Field(Role)

class Query(PublicQuery, ObjectType):
    # Reference to the current user
    # This allows the current user to query their own saved poems/etc, but not others
    me = Field(User)
    def resolve_me(root, info):
        return info.context.user

"""
Mutations
"""

class ResetProgressInput(InputObjectType):
    poemID = GlobalID()

class ResetProgress(Mutation):
    class Arguments:
        input = ResetProgressInput(required=True)
    ok = Boolean()
    def mutate(root, info, input):
        # Lookup poem and user
        poem = Node.get_node_from_global_id(info, input.poemID)
        user = info.context.user
        # Delete the progress associated with the poem and the current user
        ProgressModel.objects(user=user, poem=poem).delete()
        # Remove the poem from the user's in-progress and completed poems
        user.modify(pull__in_progress=poem, pull__completed=poem)
        return ResetProgress(ok=True)

class Logout(Mutation):
    ok = Boolean()
    def mutate(root, info):
        # Switch to a refresh token context
        info.context.verify_identity(refresh=True)
        # Construct a token block
        # We use the jti of the token to uniquely identify it
        # We also attach the expiration time so we can purge the document
        jwt = get_jwt()
        block = TokenBlocklistModel(jti=jwt['jti'], expires=datetime.fromtimestamp(jwt['exp']))
        block.save()
        return Logout(ok=True)

class Mutation(PublicMutation, ObjectType):
    reset_progress = ResetProgress.Field()
    logout = Logout.Field()

"""
Schema
"""

schema = Schema(query=Query, mutation=Mutation)
schema_loader.use_for_role(None, schema)