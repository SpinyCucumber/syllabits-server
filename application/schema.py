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
        # Retrieve one random poem using the Mongo pipeline
        pipeline = [{ '$sample': { 'size': 1 } }]
        poem_data = PoemModel.objects().aggregate(pipeline).next()
        # Convert raw data to a Poem object to automatically dereference things
        poem_obj = PoemModel._from_son(poem_data)
        return RandomPoem(poem=poem_obj)

class SubmitLineInput(InputObjectType):
    poemID = GlobalID()
    lineNum = Int()
    answer = String()

class SubmitLine(Mutation):
    class Arguments:
        input = SubmitLineInput(required=True)

    conflicts = List(Int)

    def mutate(root, info, input):
        # TODO Update user progress if user is currently logged in
        # Look up poem using Poem ID and index line
        poem = Node.get_node_from_global_id(info, input.poemID)
        line = poem.lines[input.lineNum]
        # Compare the blocks one-by-one: if there is a mismatch, record the index.
        conflicts = []
        length = min(len(line.key), len(input.answer))
        for i in range(length):
            if (line.key[i] != input.answer[i]):
                conflicts.append(i)
        # Construct response
        return SubmitLine(conflicts=conflicts)

class Mutation(ObjectType):
    random_poem = RandomPoem.Field()
    submit_line = SubmitLine.Field()

"""
Schema
"""

schema = Schema(query=Query, mutation=Mutation, types=[Poem, PoemLine, Collection, User, Progress, ProgressLine])