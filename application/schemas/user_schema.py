from graphene_mongo import MongoengineConnectionField
from graphene import (Schema, Mutation, ObjectType, InputObjectType, Boolean)
from graphene.relay import GlobalID, Node
from flask_jwt_extended import current_user

from .public_schema import Poem, Query as PublicQuery, Mutation as PublicMutation
from ..models import Progress as ProgressModel

class Query(PublicQuery, ObjectType):
    # Poems that the user has completed
    completed = MongoengineConnectionField(Poem)
    # Poems that the user are currently working on
    in_progress = MongoengineConnectionField(Poem)
    # Poems that the user has manually saved
    saved = MongoengineConnectionField(Poem)

"""
Mutations
"""

class ResetProgressInput(InputObjectType):
    poemID = GlobalID()

class ResetProgress(Mutation):
    class Arguments:
        input = ResetProgressInput(required=True)
    ok = Boolean()
    def mutate(root, info, input):
        # Lookup poem and user
        poem = Node.get_node_from_global_id(info, input.poemID)
        # Delete the progress associated with the poem and the current user
        ProgressModel.objects(user=current_user, poem=poem).delete()
        # Remove the poem from the user's in-progress and completed poems
        current_user.update(pull__in_progress=poem, pull__completed=poem)
        return ResetProgress(ok=True)

class Mutation(PublicMutation, ObjectType):
    reset_progress = ResetProgress.Field()

schema = Schema(query=Query, mutation=Mutation)