from graphene_mongo import MongoengineConnectionField
from graphene import (Schema, ObjectType)

from .base_schema import Poem, Query as BaseQuery, Mutation as BaseMutation

class Query(BaseQuery, ObjectType):
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

schema = Schema(query=Query, mutation=BaseMutation)