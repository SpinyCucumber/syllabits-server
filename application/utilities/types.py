from graphene import Field, Connection, Int, JSONString, Boolean, List, ID
from graphene.relay import Node
from graphene.types.mutation import Mutation, MutationOptions
from graphene_mongo import MongoengineObjectType
from .document_transformer import transform_document

class CountableConnection(Connection):
    """
    A connection that supports a 'totalCount' field
    """

    class Meta:
        abstract = True

    total_count = Int()

    def resolve_total_count(root, info):
        return root.iterable.count()

class MongoengineMutationOptions(MutationOptions):
    """
    Gods this is a long class name
    """
    type = None

class MongoengineMutation(Mutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, type=None, _meta=None, **options):
        assert type, 'Type is required'
        assert issubclass(type, MongoengineObjectType), 'Type must inherit from MongoengineObjectType'
        if not _meta:
            _meta = MongoengineMutationOptions(cls)
        _meta.type = type
        super().__init_subclass_with_meta__(_meta=_meta, **options)

class MongoengineCreateMutation(MongoengineMutation):
    class Meta:
        abstract = True
    
    @classmethod
    def __init_subclass_with_meta__(cls, **options):
        # Construct arguments and resulting fields
        arguments = {'data': JSONString()}
        super().__init_subclass_with_meta__(arguments=arguments, **options)
        cls._meta.fields['ok'] = Field(Boolean)

    @classmethod
    def mutate(cls, parent, info, data):
        # Create a new document instance with the supplied data
        # Mongoengine does the heavy lifting here and validates the input
        model = cls._meta.type._meta.model
        obj = model._from_son(data, created=True)
        obj.save()
        return cls(ok=True)

class MongoengineUpdateMutation(MongoengineMutation):
    class Meta:
        abstract = True
    
    @classmethod
    def __init_subclass_with_meta__(cls, **options):
        # Construct arguments and resulting fields
        arguments = {'id': ID(), 'changes': List(JSONString)}
        super().__init_subclass_with_meta__(arguments=arguments, **options)
        cls._meta.fields['ok'] = Field(Boolean)
    
    @classmethod
    def mutate(cls, parent, info, id, changes):
        # Retrieve document using global ID and apply changes
        document = Node.get_node_from_global_id(info, id, only_type=cls._meta.type)
        transform_document(document, *changes)
        document.save()
        return cls(ok=True)