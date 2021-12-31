from graphene import Field, String
from graphene.types.objecttype import ObjectType, ObjectTypeOptions
from collections import OrderedDict

class EntryOptions(ObjectTypeOptions):
    value_type = None

class Entry(ObjectType):
    class Meta:
        abstract = True
    
    @classmethod
    def __init_subclass_with_meta__(cls, value_type, **options):
        # Construct meta
        _meta = EntryOptions()
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
    entry_type = entry_type_lookup[value_type]
    # Construct new entry type if necessary
    if not entry_type:
        entry_type = Entry.create_type(f'{value_type.__name__}Entry', value_type)
        entry_type_lookup[value_type] = entry_type
    return entry_type

class MapField(Field):
    def __init__(self, value_type, **kw_args):
        # Define field type as entry type
        super(Field, self).__init__(get_entry_type(value_type), **kw_args)
