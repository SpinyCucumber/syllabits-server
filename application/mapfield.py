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
