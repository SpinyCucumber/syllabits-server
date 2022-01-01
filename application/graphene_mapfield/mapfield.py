from graphene import Field, String, List
from graphene.types.objecttype import ObjectType
from graphene.utils.thenables import maybe_thenable
from functools import partial

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