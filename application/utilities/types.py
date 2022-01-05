from graphene import Connection, Int, Mutation, List, JSONString
from graphene_mongo import MongoengineObjectType

class CountableConnection(Connection):
    """
    A connection that supports a 'totalCount' field
    """

    class Meta:
        abstract = True

    total_count = Int()

    def resolve_total_count(root, info):
        return root.iterable.count()

class CreateMutation(Mutation):
    class Meta:
        abstract = True
    
    @classmethod
    def __init_subclass_with_meta__(cls, type=None, _meta=None, **options):
        assert type, 'Type is required'
        assert issubclass(type, MongoengineObjectType), 'Type must inherit from MongoengineObjectType'
        arguments = {'changes': List(JSONString)}
        # TODO
        return super().__init_subclass_with_meta__(arguments=arguments, _meta=_meta, **options)