from collections import OrderedDict
from graphene_mongo import MongoengineConnectionField
from graphene import Field, String, List
from graphene.types.objecttype import ObjectType
from graphene.types.argument import to_arguments
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

class SearchableConnectionField(MongoengineConnectionField):
    """
    An extension of MongoengineConnectionField that supports a 'search' argument
    This allows clients to search text indexes using GraphQL
    """

    def __init__(self, type, *args, **kwargs):
        
        # Create our own custom get_queryset to process "search" and "order_by"
        def get_queryset(model, info, **args):
            search = args.pop('search', None)
            order_by = args.pop('order_by', None)
            # Construct query
            query_set = model.objects(**args)
            if search:
                query_set = query_set.search_text(search)
            if order_by:
                if order_by == 'relevance':
                    if search: query_set = query_set.order_by('$text_score')
                else:
                    query_set = query_set.order_by(order_by)
            return query_set

        super().__init__(type, *args, **kwargs, get_queryset=get_queryset)

    @property
    def args(self):
        # Override the default arguments to add that juicy search argument
        return to_arguments(
            self._base_args or OrderedDict(),
            {
                **self.field_args,
                **self.filter_args,
                **self.reference_args,
                'search': String(),
                'order_by': String()
            }
        )
    
    @args.setter
    def args(self, args):
        self._base_args = args