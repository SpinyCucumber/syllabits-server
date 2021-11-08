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
Utility
"""

def find_conflicts(key, answer):
    # Compare the blocks one-by-one: if there is a mismatch, record the index.
    conflicts = []
    length = min(len(key), len(answer))
    for i in range(length):
        if (key[i] != answer[i]):
            conflicts.append(i)
    return conflicts

"""
Types/Queries
"""

class ProgressLine(MongoengineObjectType):
    class Meta:
        model = ProgressLineModel
        interfaces = (Node,)
    # Also have to include number
    number = Int()

class Progress(MongoengineObjectType):
    class Meta:
        model = ProgressModel
        exclude_fields = ('lines',)
    lines = List(ProgressLine)
    # The lines of the poem document are actually a dictionary, with the keys
    # being strings that correspond to the line indicies. We must convert into an array
    def resolve_lines(parent, info):
        def map(key, value):
            value.number = int(key)
            return value
        return [ map(*entry) for entry in parent.lines.items() ]

class PoemLine(MongoengineObjectType):
    class Meta:
        model = PoemLineModel
        # It would be nice if this wasn't a node. But, EmbeddedDocumentListField forces this.
        # See https://github.com/graphql-python/graphene-mongo/issues/162
        interfaces = (Node,)
        # Be sure to exclude key (we don't want people automatically solving our poems!)
        exclude_fields = ('key',)
    number = Int()

class Poem(MongoengineObjectType):
    class Meta:
        model = PoemModel
        interfaces = (Node,)
        exclude_fields = ('lines',)
    progress = Field(Progress)
    # Define a custom resolver for the 'lines' field so that we can attach
    # line numbers dynamically
    lines = List(PoemLine)
    def resolve_lines(parent, info):
        lines = parent.lines
        for i in range(len(lines)):
            lines[i].number = i
        return lines
    # Only attach progress if a user is present
    def resolve_progress(parent, info):
        # Look up progress using poem and user
        if (info.context['user']):
            return ProgressModel.objects(user=info.context['user'], poem=parent).first()

class Collection(MongoengineObjectType):
    class Meta:
        model = CollectionModel
        interfaces = (Node,)
    poems = MongoengineConnectionField(Poem)
    # Returns all poems in this collection
    def resolve_poems(parent, info):
        return PoemModel.objects(collection=parent).order_by('index')

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
    correct = Boolean()

    def mutate(root, info, input):
        # Lookup poem and line
        poem = Node.get_node_from_global_id(info, input.poemID)
        line = poem.lines[input.lineNum]
        # Determine if correct
        conflicts = find_conflicts(line.key, input.answer)
        correct = (len(conflicts) == 0)
        # If the user is logged in, update their progress
        if (info.context['user']):
            query = ProgressModel.objects(user=info.context['user'], poem=poem)
            query.upsert_one(__raw__={'$set': {f'lines.{input.lineNum}': {'answer': input.answer, 'correct': correct}}})
        # Construct response
        return SubmitLine(conflicts=conflicts, correct=correct)

class LoginInput(InputObjectType):
    email = String()
    password = String()

class Login(Mutation):
    class Arguments:
        input = LoginInput(required=True)
    
    result = String()
    ok = Boolean()

    def mutate(root, info, input):
        # Attempt to find user and check if hashed passwords match
        try:
            user = UserModel.objects(email=input.email).get()
            if bcrypt.check_password_hash(user.password_hashed, input.password):
                token = create_access_token(user, additional_claims={'is_admin': user.is_admin})
                return Login(ok=True, result=token)
            else:
                return Login(ok=False)
        except UserModel.DoesNotExist:
            return Login(ok=False)

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
            token = create_access_token(user, additional_claims={'is_admin': user.is_admin})
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