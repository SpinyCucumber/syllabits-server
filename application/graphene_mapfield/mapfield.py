from graphene import Field, String, List, NonNull, Dynamic
from graphene.types.objecttype import ObjectType
from graphene.utils.thenables import maybe_thenable
from graphene_mongo.utils import get_field_description
from graphene_mongo.converter import convert_mongoengine_field
from functools import partial
import mongoengine

entry_type_lookup = {}

def get_entry_type(value_type):
    name = value_type._meta.name
    entry_type = entry_type_lookup.get(name, None)
    # Construct new entry type if necessary
    if not entry_type:
        class Entry(ObjectType):
            key = String()
            value = Field(value_type)
        entry_type = type(f'{name}Entry', (Entry,), {})
        entry_type_lookup[name] = entry_type
    return entry_type

class MapField(Field):

    def __init__(self, value_type, **kw_args):
        # Define field type as entry type
        _type = List(get_entry_type(value_type))
        super(MapField, self).__init__(_type, **kw_args)

    @classmethod
    def resolve_connection(cls, resolved):
        # "Flatten" map
        return [{'key': k, 'value': v} for (k, v) in resolved.items()]

    @classmethod
    def map_resolver(cls, resolver, root, info, **args):
        resolved = resolver(root, info, **args)
        on_resolve = partial(cls.resolve_map)
        return maybe_thenable(resolved, on_resolve)

    def get_resolver(self, parent_resolver):
        resolver = super(MapField, self).get_resolver(parent_resolver)
        return partial(self.map_resolver, resolver)

# Associate Mongoengine MapFields with our custom MapField for automatic conversion
@convert_mongoengine_field.register(mongoengine.MapField)
def convert_mapfield(field, registry=None):
    base_type = convert_mongoengine_field(field.field, registry=registry)
    if isinstance(base_type, (Dynamic)):
        base_type = base_type.get_type()
        if base_type is None:
            return
        base_type = base_type._type
    # Non-relationship field
    relations = (mongoengine.ReferenceField, mongoengine.EmbeddedDocumentField)
    if not isinstance(base_type, (List, NonNull)) and not isinstance(
        field.field, relations
    ):
        base_type = type(base_type)
    return MapField(
        value_type=base_type,
        description=get_field_description(field, registry),
        required = field.required
    )