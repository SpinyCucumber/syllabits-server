from mongoengine.base import BaseDocument, EmbeddedDocumentList, BaseList
from mongoengine.errors import DoesNotExist

_lookup = {}
    
def register(name, supports=None, required_args=None):
    """
    Registers new functions as operators by decorating them
    Operators have a name, a set of supported types, and a list of required keyword args.
    """
    def wrapper(func):
        def wrapped(receiver, **kwargs):
            # Check receiver type
            if not isinstance(receiver, supports):
                raise TypeError(f'Operator \'{name}\' does not support type \'{type(receiver).__name__}\'')
            # Check that arguments are present and match type
            for arg in required_args:
                if arg not in kwargs:
                    raise TypeError(f'Missing required arg \'{arg}\'')
            return func(receiver, **kwargs)
        _lookup[name] = wrapped
        return wrapped
    return wrapper

def get(name):
    """
    Returns operator corresponding to 'name', or None
    """
    return _lookup.get(name, None)

@register('set', supports=(BaseDocument,), required_args=('field', 'value'))
def set(receiver: BaseDocument, field=None, value=None):
    """
    Sets a field of a document to a value
    """
    receiver[field] = value

@register('create', supports=(EmbeddedDocumentList,), required_args=('data',))
def create(receiver: EmbeddedDocumentList, data=None):
    """
    Inserts a new document into an embedded document list
    """
    receiver.create(**data)

@register('delete', supports=(EmbeddedDocumentList,), required_args=('where',))
def delete(receiver: EmbeddedDocumentList, where=None):
    """
    Deletes documents that meet certain conditions from an embedded document list
    """
    receiver.filter(**where).delete()

@register('create_ref', supports=(BaseList,), required_args=('id',))
def create_ref(receiver: BaseList, id=None):
    """
    Adds a document to a reference list
    Also updates the reference count of the referenced document.
    """
    # Determine referenced document type
    document_type = receiver._instance._fields[receiver._name].field.document_type_obj
    # Upsert document and increment ref count, then add to list
    document = document_type.objects.filter(pk=id).upsert_one(inc__ref_count=1)
    receiver.append(document)

@register('delete_ref', supports=(BaseList,), required_args=('id',))
def delete_ref(receiver: BaseList, id=None):
    """
    Removed a document from a reference list
    Also updates the reference count of the referenced document.
    """
    # Determine referenced document type
    document_type = receiver._instance._fields[receiver._name].field.document_type_obj
    # Upsert document and decrement ref count, then remove from list
    document = document_type.objects.filter(pk=id).upsert_one(inc__ref_count=1)
    receiver.remove(document)

@register('add', supports=(list,), required_args=('value',))
def add(receiver: list, value=None):
    """
    Adds a value to a list
    """
    receiver.append(value)

@register('remove', supports=(list,), required_args=('value',))
def remove(receiver: list, value=None):
    """
    Removes a value from a list
    """
    receiver.remove(value)