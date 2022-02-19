from graphene import Field, Connection, Int, JSONString, Boolean, List, ID
from graphene.relay import Node, GlobalID
from graphene.types.mutation import Mutation, MutationOptions
from graphene_mongo import MongoengineObjectType
import re
import signals
from .document_path import DocumentPath
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
        document = model._from_son(data, created=True)
        # Send signal then create document
        signals.pre_create.send(model, document=document)
        document.save()
        return cls(ok=True, id=document.id)

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

        # Retrieve document using global ID
        document = Node.get_node_from_global_id(info, id, only_type=cls._meta.type)
        model = cls._meta.type._meta.model
        receiver_lookup = {}

        for transform in transforms:
            # Parse operation using operation registry
            op_name = transform.pop('op', None)
            if not op_name:
                raise TypeError('All transforms must provide the \'op\' attribute')
            operator = operators.get(op_name)
            if not operator:
                raise TypeError(f'Unknown operation \'{op_name}\'')

            # Parse path
            # If path is specified, we try to lookup receiver using cache
            # If not, we compile path and evaluate to find receiver
            raw_path = transform.pop('path', '')
            receiver = receiver_lookup.get(raw_path, None)
            if not receiver:
                path = DocumentPath(raw_path)
                # Must fix field names
                for level in path.levels:
                    level.field = fix_field_name(level.field)
                receiver = path.evaluate(document)
                receiver_lookup[raw_path] = receiver
            
            # Remaining values are arguments
            # 'Fix' arguments depending on operation
            # It's not the prettiest, but it's simple, and I dread thinking of the alternatives
            args = transform
            if operator == operators.set:
                args['field'] = fix_field_name(args['field'])
                field = receiver._fields[args['field']]
                args['value'] = field.to_python(args['value'])
            elif operator in (operators.add, operators.remove):
                field = receiver._instance._fields[receiver._name].field
                args['value'] = field.to_python(args['value'])
            elif operator == operator.create:
                args['data'] = fix_fields(args['data'])
            elif operator == operator.delete:
                args['where'] = fix_fields(args['where'])
            
            # Send update signal
            signals.pre_update.send(model, document=document, operator=operator, receiver=receiver, args=args)

            # Apply transform
            operator(receiver, **args)

        # Save document to database
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
        # Send signal then delete document
        model = cls._meta.type._meta.model
        signals.pre_delete.send(model, document=document)
        document.delete()
        return cls(ok=True)