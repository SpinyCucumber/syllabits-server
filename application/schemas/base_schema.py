from graphene.types.scalars import Boolean
from graphene_mongo import MongoengineObjectType, MongoengineConnectionField
from graphene.relay import Node, GlobalID
from graphene import (ObjectType, Mutation, Schema, Field, InputObjectType, Int, String, List, Enum)
from flask_jwt_extended import create_access_token
from mongoengine.errors import NotUniqueError

from ..models import (
    Collection as CollectionModel,
    PoemLine as PoemLineModel,
    Poem as PoemModel,
    User as UserModel,
    Progress as ProgressModel,
    ProgressLine as ProgressLineModel
)

from ..extensions import bcrypt

"""
Types/Queries
"""

class PoemLine(MongoengineObjectType):
    class Meta:
        model = PoemLineModel
        # It would be nice if this wasn't a node. But, EmbeddedDocumentListField forces this.
        # See https://github.com/graphql-python/graphene-mongo/issues/162
        interfaces = (Node,)
    number = Int()

class Poem(MongoengineObjectType):
    class Meta:
        model = PoemModel
        interfaces = (Node,)
        exclude_fields = ('lines',)
    # Define a custom resolver for the 'lines' field so that we can attach
    # line numbers dynamically
    lines = List(PoemLine)
    def resolve_lines(parent, info):
        lines = parent.lines
        for i in range(len(lines)):
            lines[i].number = i
        return lines

class Collection(MongoengineObjectType):
    class Meta:
        model = CollectionModel
        interfaces = (Node,)
    poems = MongoengineConnectionField(Poem)
    # Returns all poems in this collection
    def resolve_poems(parent, info):
        return PoemModel.objects(collection=parent).order_by('index')

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

class LoginInput(InputObjectType):
    email = String()
    password = String()

class Login(Mutation):
    class Arguments:
        input = LoginInput(required=True)
    
    token = String()
    ok = Boolean()

    def mutate(root, info, input):
        # TODO
        return Login(token=None)

class RegisterInput(LoginInput):
    pass

class RegisterError(Enum):
    USER_EXISTS = 'USER_EXISTS'

class Register(Mutation):
    class Arguments:
        input = RegisterInput(required=True)
    
    result = String()
    ok = Boolean()
    error = Field(RegisterError)

    def mutate(root, info, input):
        # Create new user with email and attempt to save
        # Save before hashing password as hashing is expensive
        user = UserModel(email=input.email)
        try:
            user.save()
            password_hashed = bcrypt.generate_password_hash(input.password).decode('utf-8')
            user.password_hashed = password_hashed
            user.save()
            # Create new token
            token = create_access_token(identity=user.id, additional_claims={'admin': user.is_admin})
            return Register(ok=True, result=token)
        except NotUniqueError:
            return Register(ok=False, error=RegisterError.USER_EXISTS)

class Mutation(ObjectType):
    random_poem = RandomPoem.Field()
    submit_line = SubmitLine.Field()
    login = Login.Field()
    register = Register.Field()

"""
Schema
"""

schema = Schema(query=Query, mutation=Mutation)