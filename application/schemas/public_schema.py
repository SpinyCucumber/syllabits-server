from graphene.types.scalars import Boolean
from graphene_mongo import MongoengineObjectType, MongoengineConnectionField
from graphene.relay import Node, GlobalID
from graphene import (ObjectType, Mutation, Schema, Field, InputObjectType, Int, String, Float, List, Enum)
from flask import current_app as app
from flask_jwt_extended import create_access_token, create_refresh_token, verify_jwt_in_request, set_refresh_cookies, current_user
from flask_jwt_extended.exceptions import NoAuthorizationError
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
        interfaces = (Node,)
        exclude_fields = ('lines',)
    # The lines of the poem document are actually a dictionary, with the keys
    # being strings that correspond to the line indicies. We must convert into an array
    lines = List(ProgressLine)
    def resolve_lines(parent, info):
        def map(key, value):
            value.number = int(key)
            return value
        return [ map(*entry) for entry in parent.lines.items() ]
    # We also define a 'completion' field that returns a percent complete for convenience
    completion = Float()
    def resolve_completion(parent, info):
        return parent.num_correct / len(parent.poem.lines)

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
    # Expose number of lines for convenience
    num_lines = Int()
    # Define a custom resolver for the 'lines' field so that we can attach
    # line numbers dynamically
    lines = List(PoemLine)
    def resolve_lines(parent, info):
        lines = parent.lines
        for i in range(len(lines)):
            lines[i].number = i
        return lines
    def resolve_num_lines(parent, info):
        return len(parent.lines)
    # Only attach progress if a user is present
    def resolve_progress(parent, info):
        # Look up progress using poem and user
        if (current_user):
            return ProgressModel.objects(user=current_user, poem=parent).first()

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
        if (current_user):
            progress_query = ProgressModel.objects(user=current_user, poem=poem)
            # Construct update clause and upsert progress (insert or update)
            update_clause = {'$set': {f'lines.{input.lineNum}': {'answer': input.answer, 'correct': correct}}}
            if (correct): update_clause['$inc'] = {'num_correct': 1}
            progress = progress_query.upsert_one(__raw__=update_clause)
            # Determine if poem is complete
            # If poem is complete, remove in_progress and add complete
            # If not, add in_progress
            complete = (progress.num_correct == len(poem.lines))
            if complete:
                current_user.update(pull__in_progress=poem, add_to_set__completed=poem)
            else:
                current_user.update(add_to_set__in_progress=poem)
            
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
                # Create new access token and set refresh token in cookies
                token = create_access_token(user)
                # TODO Pass cookie to response using info context
                # refresh_token = create_refresh_token(user)
                # set_refresh_cookies(info.context, refresh_token)
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
        user = UserModel(email=input.email, is_admin=False)
        try:
            user.save()
            password_hashed = bcrypt.generate_password_hash(input.password).decode('utf-8')
            user.password_hashed = password_hashed
            user.save()
            # Create new access token and set refresh token in cookies
            access_token = create_access_token(user)
            # TODO Pass cookie to response using info context
            # refresh_token = create_refresh_token(user)
            # set_refresh_cookies(info.context, refresh_token)
            return Register(ok=True, result=access_token)
        except NotUniqueError:
            return Register(ok=False, error=RegisterError.USER_EXISTS)

"""
Creates a new access token using the user's refresh token
"""
class Refresh(Mutation):
    ok = Boolean()
    result = String()
    def mutate(root, info, input):
        # Use verify_jwt_in_request to check presence of refresh token in cookies
        # This creates a new "JWT context" which updates the current_user
        # If refresh token is present, create new access token and return it
        # If not, return not ok
        try:
            verify_jwt_in_request(refresh=True, locations='cookies')
            token = create_access_token(current_user)
            return Refresh(ok=True, result=token)
        except NoAuthorizationError:
            return Refresh(ok=False)

class Mutation(ObjectType):
    random_poem = RandomPoem.Field()
    submit_line = SubmitLine.Field()
    login = Login.Field()
    register = Register.Field()
    refresh = Refresh.Field()

"""
Schema
"""

schema = Schema(query=Query, mutation=Mutation)