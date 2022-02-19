from graphene_mongo import MongoengineObjectType
from graphene import (Node, GlobalID, ObjectType, Mutation, Schema, Field, InputObjectType, Int, String, List, Enum, Boolean)
from graphene_mongo import MongoengineConnectionField
import mongoengine

from ..models import (
    Category as CategoryModel,
    Collection as CollectionModel,
    PoemLine as PoemLineModel,
    Poem as PoemModel,
    User as UserModel,
    Progress as ProgressModel,
    ProgressLine as ProgressLineModel,
)
from ..extensions import bcrypt
from ..utilities import CountableConnection, find_conflicts, decode_location, encode_location
from ..exceptions import InsufficientPrivilegeError

"""
Types/Queries
"""

class Category(MongoengineObjectType):
    class Meta:
        model = CategoryModel
        interfaces = (Node,)
        connection_class = CountableConnection
        filter_fields = {
            'name': ['startswith', 'nin', 'in']
        }

class ProgressLine(MongoengineObjectType):
    class Meta:
        model = ProgressLineModel

class Progress(MongoengineObjectType):
    class Meta:
        model = ProgressModel

class PoemLine(MongoengineObjectType):
    """
    Semantically, inheriting Node means an object is "globally identifiable" with its ID.
    This is not possible with poems, as poem lines are embedded inside poems and are only unique within that poem.
    So, we don't inherit Node.
    """
    class Meta:
        model = PoemLineModel
        # It would be nice if this wasn't a node. But, EmbeddedDocumentListField forces this.
        # See https://github.com/graphql-python/graphene-mongo/issues/162
        # interfaces = (Node,)
    num_feet = Int()
    # To read the key, users must have admin status
    def resolve_key(parent, info):
        if getattr(info.context.user, 'is_admin', None):
            return parent.key
        raise InsufficientPrivilegeError('Not authorized')
    # Also expose number of feet so client knows how many slots to render
    def resolve_num_feet(parent, info):
        return len(parent.key)

class Poem(MongoengineObjectType):
    class Meta:
        model = PoemModel
        interfaces = (Node,)
        connection_class = CountableConnection
        filter_fields = {
            'categories': ['all', 'in']
        }
        searchable = True

    progress = Field(Progress)
    lines = List(PoemLine)
    categories = List(String)
    location = String()
    num_lines = Int() # Expose number of lines for convenience

    def resolve_num_lines(parent, info):
        return len(parent.lines)
    
    # Only attach progress if a user is present
    def resolve_progress(parent, info):
        # Look up progress using poem and user
        user = info.context.user
        if (user):
            return ProgressModel.objects(user=user, poem=parent).first()

    # The location last used to access a poem
    # Only resolve if user is present
    def resolve_location(parent, info):
        user = info.context.user
        if (user):
            return user.locations.get(str(parent.id))

class Collection(MongoengineObjectType):
    class Meta:
        model = CollectionModel
        interfaces = (Node,)
        connection_class = CountableConnection
        searchable = True

class Query(ObjectType):
    node = Node.Field()
    collections = MongoengineConnectionField(Collection)
    poems = MongoengineConnectionField(Poem)
    categories = MongoengineConnectionField(Category)

"""
Mutations
"""

class RandomPoem(Mutation):
    poem = Field(Poem)
    
    def mutate(parent, info):
        # Retrieve one random poem using the Mongo pipeline
        pipeline = [{ '$sample': { 'size': 1 } }]
        poem_data = PoemModel.objects().aggregate(pipeline).next()
        # Convert raw data to a Poem object to automatically dereference things
        poem_obj = PoemModel._from_son(poem_data)
        return RandomPoem(poem=poem_obj)

class LocationType(Enum):
    DIRECT = 0
    COLLECTION = 1

class PlayPoem(Mutation):
    """
    There are several ways to locate a poem.
    One way is to directly use the ID of a poem.
    Another way is to identity a collection and specify an index.
    Since GraphQL doesn't support polymorphic inputs, a simple solution is to use Strings,
    and "bypass" the schema. It would be great if GraphQL could accomodate polymorphic inputs,
    but this is the next best thing.

    This mutation takes a location and "resolves" it, returning a poem
    A location can also provide information about "next" and "previous" poems, which
    allows users to navigate
    """

    class Arguments:
        location = String(required=True)
    poem = Field(Poem)
    next = String()
    previous = String()

    def mutate(parent, info, location):
        # Resolve location
        # Locations are B64-encoded JSON. A 'type' field specifies whether the location is
        # "direct" or references a collection.
        decoded = decode_location(location)
        next = None
        previous = None
        if decoded['t'] == LocationType.DIRECT:
            poem=Node.get_node_from_global_id(info, decoded['p'])
        elif decoded['t'] == LocationType.COLLECTION:
            collection = Node.get_node_from_global_id(info, decoded['c'])
            poem = collection.poems[decoded['i']]
            # Define next and previous locations, if applicable
            if decoded['i'] > 0:
                previous = decoded.copy()
                previous['i'] -= 1
                previous = encode_location(previous)
            if decoded['i'] < (collection.poems.length - 1):
                next = decoded.copy()
                next['i'] += 1
                next = encode_location(next)
        # If user is logged in, update 'last played location'
        user = info.context.user
        if (user):
            update_clause = {'$set': {f'locations.{str(poem.id)}': location}}
            user.modify(__raw__=update_clause)
        # Package result
        return PlayPoem(poem=poem, next=next, previous=previous)

class SubmitLineInput(InputObjectType):
    poemID = GlobalID()
    lineID = String()
    answer = List(String)

class SubmitLine(Mutation):
    class Arguments:
        input = SubmitLineInput(required=True)

    conflicts = List(Int)
    correct = Boolean()

    def mutate(parent, info, input):
        # Lookup poem and line
        poem = Node.get_node_from_global_id(info, input.poemID)
        line = poem.lines.get(id=input.lineID)
        # Determine if correct
        conflicts = None
        if len(line.key) == len(input.answer):
            conflicts = find_conflicts(line.key, input.answer)
            correct = (len(conflicts) == 0)
        else:
            correct = False
        # If the user is logged in, update their progress
        user = info.context.user
        if (user):
            progress_query = ProgressModel.objects(user=user, poem=poem)
            # Construct update clause and upsert progress (insert or update)
            update_clause = {'$set': {f'lines.{input.lineID}': {'answer': input.answer, 'correct': correct}}}
            if (correct): update_clause['$inc'] = {'num_correct': 1}
            progress = progress_query.upsert_one(__raw__=update_clause)
            # Determine if poem is complete
            # If poem is complete, remove in_progress and add complete
            # If not, add in_progress
            complete = (progress.num_correct == len(poem.lines))
            if complete:
                user.modify(pull__in_progress=poem, add_to_set__completed=poem)
            else:
                user.modify(add_to_set__in_progress=poem)
            
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

    def mutate(parent, info, input):
        # Attempt to find user and check if hashed passwords match
        try:
            user = UserModel.objects(email=input.email).get()
            if bcrypt.check_password_hash(user.password_hashed, input.password):
                # Update context with new user and request a refresh token
                # to be attached to the response
                info.context.user = user
                info.context.request_refresh()
                token = info.context.create_access_token()
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

    def mutate(parent, info, input):
        # Create new user with email and attempt to save
        user = UserModel(email=input.email, is_admin=False)
        password_hashed = bcrypt.generate_password_hash(input.password).decode('utf-8')
        user.password_hashed = password_hashed
        try:
            user.save()
            # Update context with new user and request a refresh token
            # to be attached to the response
            info.context.user = user
            info.context.request_refresh()
            token = info.context.create_access_token()
            return Register(ok=True, result=token)
        except mongoengine.errors.NotUniqueError:
            return Register(ok=False, error=RegisterError.USER_EXISTS)

class Refresh(Mutation):
    """
    Creates a new access token using the user's refresh token
    """

    ok = Boolean()
    result = String()
    def mutate(parent, info):
        # Verify identity using refresh token
        info.context.verify_identity(refresh=True)
        # If identity is verified, create new access token
        if info.context.user:
            token = info.context.create_access_token()
            return Refresh(ok=True, result=token)
        return Refresh(ok=False)

class Mutation(ObjectType):
    play_poem = PlayPoem.Field()
    random_poem = RandomPoem.Field()
    submit_line = SubmitLine.Field()
    login = Login.Field()
    register = Register.Field()
    refresh = Refresh.Field()

"""
Schema
"""

schema = Schema(query=Query, mutation=Mutation)