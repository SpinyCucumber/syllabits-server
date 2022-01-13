from graphene import Field, Connection, Int, JSONString, Boolean, List, ID
from graphene.relay import Node
from graphene.types.mutation import Mutation, MutationOptions
from graphene_mongo import MongoengineObjectType
from .document_path import DocumentPath
from .document_transform import operators, DocumentTransform

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
    """
    Accepts a list of transforms and applies them to a Mongoengine document
    A 'transform' is a dict that (at minimum) specifies the 'op' attribute, which denotes the type of operation.
    A transform can additionally specify the 'path' attribute, which is a DocumentPath that is evaluated to change
    the operation receiver.
    The rest of the attributes are arguments to the operation.
    """
    class Meta:
        abstract = True
    
    @classmethod
    def __init_subclass_with_meta__(cls, **options):
        # Construct arguments and resulting fields
        arguments = {'id': ID(), 'transforms': List(JSONString)}
        super().__init_subclass_with_meta__(arguments=arguments, **options)
        cls._meta.fields['ok'] = Field(Boolean)
    
    @classmethod
    def mutate(cls, parent, info, id, transforms):

        receiver_lookup = {}
        def parse_transform(transform: dict):
            # Parse operation using operation registry
            op_name = transform.pop('op', None)
            if not op_name:
                raise TypeError('All transforms must provide the \'op\' attribute')
            operator = operators.get(op_name)
            if not operator:
                raise TypeError(f'Unknown operation \'{op_name}\'')
            # Parse path
            # If path is specified, we try to lookup using cache first
            # If cache lookup fails, we parse raw path and evaluate on document
            # to find receiver
            path = transform.pop('path', None)
            if path:
                receiver = receiver_lookup.get(path, None)
                if not receiver:
                    compiled_path = DocumentPath(path)
                    # TODO Convert each path field to snake case
                    receiver = compiled_path.evaluate(document)
                    receiver_lookup[path] = receiver
            # The remaining attributes are operation arguments
            return DocumentTransform(operator, path, transform)

        # Retrieve document using global ID
        document = Node.get_node_from_global_id(info, id, only_type=cls._meta.type)
        # Parse each transform and apply to document, then save document
        for transform in map(parse_transform, transforms):
            transform.apply(document)
        document.save()
        return cls(ok=True)