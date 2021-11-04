from flask_jwt_extended import current_user
from graphene_mongo import MongoengineObjectType
from graphene.relay import Node
from graphene import (ObjectType, Schema, Mutation)

from ..models import User as UserModel, Progress as ProgressModel, ProgressLine as ProgressLineModel
from .base_schema import SubmitLine, Query as BaseQuery, Mutation as BaseMutation

class User(MongoengineObjectType):
    class Meta:
        model = UserModel
        interfaces = (Node,)

class ProgressLine(MongoengineObjectType):
    class Meta:
        model = ProgressLineModel
        interfaces = (Node,)

class Progress(MongoengineObjectType):
    class Meta:
        model = ProgressModel

# This mutation overrides the base SubmitLine mutation
# to save the user's progress before checking the actual line.
class UserSubmitLine(SubmitLine):
    def mutate(root, info, input):
        # Update user progress
        poem = Node.get_node_from_global_id(info, input.poemID)
        query = ProgressModel.objects(user=info.context['user'], poem=poem)
        query.upsert_one(__raw__={'$set': {f'lines.{input.lineNum}.answer': input.answer}})
        # Normal submit logic
        return SubmitLine.mutate(root, info, input)

# Inherit from base mutation set
class Mutation(BaseMutation, ObjectType):
    # Override
    submitLine = UserSubmitLine.Field()

schema = Schema(query=BaseQuery, mutation=Mutation)