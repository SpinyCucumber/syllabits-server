from mongoengine.base import BaseDocument, EmbeddedDocumentList

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