from graphene_mongo import MongoengineConnectionField
from graphene import (Schema, Mutation, ObjectType, InputObjectType, Boolean)
from graphene.relay import GlobalID, Node

from .public_schema import Poem, Query as PublicQuery, Mutation as PublicMutation
from ..models import Progress as ProgressModel

class Query(PublicQuery, ObjectType):
    # Poems that the user has completed
    completed_poems = MongoengineConnectionField(Poem)
    # Poems that the user are currently working on
    poems_in_progress = MongoengineConnectionField(Poem)
    # Poems that the user has manually saved
    saved_poems = MongoengineConnectionField(Poem)

    def resolve_completed_poems(parent, info):
        return info.context['user'].completed

    def resolve_poems_in_progress(parent, info):
        return info.context['user'].in_progress
    
    def resolve_saved_poems(parent, info):
        return info.context['user'].saved

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
        user = info.context['user']
        poem = Node.get_node_from_global_id(info, input.poemID)
        # Delete the progress associated with the poem and the current user
        ProgressModel.objects(user=user, poem=poem).delete()
        # Remove the poem from the user's in-progress and completed poems
        user.update(pull__in_progress=poem, pull__completed=poem)
        return ResetProgress(ok=True)

class Mutation(PublicMutation, ObjectType):
    reset_progress = ResetProgress.Field()

schema = Schema(query=Query, mutation=Mutation)