from graphene_mongo import MongoengineObjectType, MongoengineConnectionField
from graphene import (Field, Schema, ObjectType)
from graphene.relay import Node

from ..models import User as UserModel, Progress as ProgressModel
from .base_schema import Progress, Query as BaseQuery, Mutation as BaseMutation

class Query(BaseQuery, ObjectType):
    # All 'progress' documents associated with the current user
    my_progress = MongoengineConnectionField(Progress)

    def resolve_my_progress(parent, info):
        return ProgressModel.objects(user = info.context['user'])

schema = Schema(query=Query, mutation=BaseMutation)