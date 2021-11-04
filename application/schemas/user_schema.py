from graphene_mongo import MongoengineObjectType
from graphene.relay import Node
from graphene import (Schema)

from ..models import User as UserModel
from .base_schema import Query as BaseQuery, Mutation as BaseMutation

class User(MongoengineObjectType):
    class Meta:
        model = UserModel
        interfaces = (Node,)

schema = Schema(query=BaseQuery, mutation=BaseMutation)