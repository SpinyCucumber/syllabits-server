from graphene_mongo import MongoengineObjectType, MongoengineConnectionField
from graphene.relay import Node, GlobalID
from graphene import (ObjectType, Mutation, Schema, Field, InputObjectType, Int, String, Boolean, List)

from .models import (
    Collection as CollectionModel,
    PoemLine as PoemLineModel,
    Poem as PoemModel,
    User as UserModel,
    Progress as ProgressModel,
    ProgressLine as ProgressLineModel
)

"""
Types/Queries
"""

class PoemLine(MongoengineObjectType):
    class Meta:
        model = PoemLineModel
        # It would be nice if this wasn't a node. But, EmbeddedDocumentListField forces this.
        # See https://github.com/graphql-python/graphene-mongo/issues/162
        interfaces = (Node,)

class Poem(MongoengineObjectType):
    class Meta:
        model = PoemModel
        interfaces = (Node,)

class Collection(MongoengineObjectType):
    class Meta:
        model = CollectionModel
        interfaces = (Node,)
    poems = MongoengineConnectionField(Poem)
    # TODO Resolver

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

class Query(ObjectType):
    node = Node.Field()
    all_collections = MongoengineConnectionField(Collection)
    all_poems = MongoengineConnectionField(Poem)

"""
Mutations
"""

class RandomPoem(Mutation):
    poem = Field(Poem)
    
    def mutate(root, info):
        # TODO
        pass

class SubmitLineInput(InputObjectType):
    poemID = GlobalID()
    lineNum = Int()
    answer = String()

class SubmitLine(Mutation):
    class Arguments:
        input = SubmitLineInput(required=True)

    correct = Boolean()
    hints = List(Int)

    def mutate(root, info, input):
        # TODO
        pass

class Mutation(ObjectType):
    random_poem = RandomPoem.Field()
    submit_line = SubmitLine.Field()

"""
Schema
"""

schema = Schema(query=Query, mutation=Mutation, types=[Poem, PoemLine, Collection, User, Progress, ProgressLine])