from graphene import Field, Connection, Int, JSONString, Boolean, List, ID
from graphene.relay import Node, GlobalID
from graphene.types.mutation import Mutation, MutationOptions
from graphene_mongo import MongoengineObjectType
import re
from .document_path import DocumentPath
from .document_transform import DocumentTransform
from . import operators

PATTERN = re.compile(r'(?<!^)(?=[A-Z])')
def fix_field_name(name):
    return PATTERN.sub('_', name).lower()

def fix_fields(value):
    if isinstance(value, dict):
        return {fix_field_name(k): fix_fields(v) for k, v in value.items()}
    if isinstance(value, list):
        return [fix_fields(e) for e in value]
    return value

arg_fixers = {
    operators.create: {'data': fix_fields},
    operators.delete: {'where': fix_fields},
    operators.set: {'field': fix_field_name},
}

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
        # We return the ID of the newly created document
        arguments = {'data': JSONString()}
        super().__init_subclass_with_meta__(arguments=arguments, **options)
        cls._meta.fields['ok'] = Field(Boolean)
        cls._meta.fields['id'] = GlobalID(node=None, parent_type=cls._meta.type)

    @classmethod
    def mutate(cls, parent, info, data):
        # Create a new document instance with the supplied data
        # Mongoengine does the heavy lifting here and validates the input
        # Must correct data field names
        data = fix_fields(data)
        model = cls._meta.type._meta.model
        doc = model._from_son(data, created=True)
        doc.save()
        return cls(ok=True, id=doc.id)

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

        path_lookup = {}
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
            # If cache lookup fails, we parse raw path to create compiled path
            raw_path = transform.pop('path', '')
            path = path_lookup.get(raw_path, None)
            if not path:
                path = DocumentPath(raw_path)
                # Convert each path field to snake case
                for level in path.levels:
                    level.field = fix_field_name(level.field)
                path_lookup[raw_path] = path
            # Apply fixers
            args = transform
            fixers = arg_fixers.get(operator, None)
            if fixers:
                for param, fixer in fixers.items():
                    args[param] = fixer(args[param])
            # The remaining attributes are operation arguments
            return DocumentTransform(operator, path, args)

        # Retrieve document using global ID
        document = Node.get_node_from_global_id(info, id, only_type=cls._meta.type)
        # Parse each transform and apply to document, then save document
        for transform in map(parse_transform, transforms):
            transform.apply(document)
        document.save()
        return cls(ok=True)

class MongoengineDeleteMutation(MongoengineMutation):

    class Meta:
        abstract = True
    
    @classmethod
    def __init_subclass_with_meta__(cls, **options):
        # Construct arguments and resulting fields
        arguments = {'id': ID()}
        super().__init_subclass_with_meta__(arguments=arguments, **options)
        cls._meta.fields['ok'] = Field(Boolean)
    
    @classmethod
    def mutate(cls, parent, info, id):
        # Retrieve document using global ID and delete
        document = Node.get_node_from_global_id(info, id, only_type=cls._meta.type)
        document.delete()
        return cls(ok=True)