from graphene import Field, String, List
from graphene.types.objecttype import ObjectType, ObjectTypeOptions
from graphene.utils.thenables import maybe_thenable
from functools import partial
from collections import OrderedDict

class EntryOptions(ObjectTypeOptions):
    value_type = None

class Entry(ObjectType):
    class Meta:
        abstract = True
    
    @classmethod
    def __init_subclass_with_meta__(cls, value_type=None, **options):
        # Construct meta
        _meta = EntryOptions(cls)
        _meta.value_type = value_type
        _meta.fields = OrderedDict([
            ("key", Field(String)),
            ("value", Field(value_type))
        ])
        return super(Entry, cls).__init_subclass_with_meta__(
            _meta=_meta, **options
        )

entry_type_lookup = {}

def get_entry_type(value_type):
    entry_type = entry_type_lookup.get(value_type, None)
    # Construct new entry type if necessary
    if not entry_type:
        entry_type = Entry.create_type(f'{value_type.__name__}Entry', value_type=value_type)
        entry_type_lookup[value_type] = entry_type
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
