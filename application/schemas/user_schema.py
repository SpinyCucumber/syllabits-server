from flask_jwt_extended import current_user
from graphene_mongo import MongoengineObjectType
from graphene.relay import Node
from graphene import (ObjectType, Schema, Mutation)

from ..models import User as UserModel
from .base_schema import SubmitLine, Query as BaseQuery, Mutation as BaseMutation

class User(MongoengineObjectType):
    class Meta:
        model = UserModel
        interfaces = (Node,)

class UserSubmitLine(SubmitLine):
    # Override
    def mutate(root, info, input):
        # TODO Update user progress
        return SubmitLine.mutate(root, info, input)

# Inherit from base mutation set
class Mutation(BaseMutation, ObjectType):
    # Override
    submitLine = UserSubmitLine.Field()

schema = Schema(query=BaseQuery, mutation=Mutation)