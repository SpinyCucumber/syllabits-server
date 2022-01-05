from graphene import Field, Connection, Int, JSONString, Boolean
from graphene.types.mutation import Mutation, MutationOptions
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

class MongoengineCreateMutationOptions(MutationOptions):
    """
    Gods this is a long class name
    """
    type = None

class MongoengineCreateMutation(Mutation):
    """
    A simple mutation class that supports creating a new instance of a Mongoengine document
    The user provides data in an unrestricted JSON format, and the data is validated by Mongoengine.
    """
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, type=None, _meta=None, **options):
        assert type, 'Type is required'
        assert issubclass(type, MongoengineObjectType), 'Type must inherit from MongoengineObjectType'

        if not _meta:
            _meta = MongoengineCreateMutationOptions(cls)
        _meta.type = type

        # Construct mutation arguments and resulting fields
        arguments = {'data': JSONString()}
        super().__init_subclass_with_meta__(arguments=arguments, _meta=_meta, **options)
        _meta.fields['ok'] = Field(Boolean)

    @classmethod
    def mutate(cls, parent, info, data):
        # Create a new document instance with the supplied data
        # Mongoengine does the heavy lifting here and validates the input
        model = cls._meta.type._meta.model
        obj = model._from_son(data, created=True)
        obj.save()
        return cls(ok=True)