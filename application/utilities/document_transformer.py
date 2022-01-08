from mongoengine.base import BaseDocument, EmbeddedDocumentList
from .document_path import DocumentPath

operater_lookup = {}

def operator(name, supported_types=None, required_args=None):
    """
    When used as a decorator, registers a function as an operator.
    Operators have a name, a set of supported types, and a list of required keyword args.
    """
    def wrapper(func):
        def wrapped(receiver, **kwargs):
            # Check receiver type
            if not isinstance(receiver, supported_types):
                raise TypeError(f'Operator \'{name}\' does not support type \'{type(receiver).__name__}\'')
            # Check required args
            for arg in required_args:
                if arg not in kwargs:
                    raise TypeError(f'Missing required arg \'{arg}\'')
            return func(receiver, **kwargs)
        operater_lookup[name] = wrapped
        return wrapped
    return wrapper

@operator('set', supported_types=(BaseDocument, ), required_args=('field', 'value'))
def set(receiver, field=None, value=None):
    receiver[field] = value

def transform_document(document, changes):
    path_cache = {}
    for change in changes:
        copy = change.copy()
        # Determine operation
        op_name = copy.pop('op', None)
        if not op_name:
            raise TypeError('All changes must provide the \'op\' attribute')
        operator = operater_lookup.get(op_name, None)
        if not operator:
            raise TypeError(f'Unknown operation \'{op_name}\'')
        # Determine operation receiver
        receiver = document
        path = copy.pop('path', None)
        # If path is specified, we try to lookup using cache first
        if path:
            receiver = path_cache.get(path, None)
            if not receiver:
                receiver = DocumentPath(path).evaluate(document)
                path_cache[path] = receiver
        # Apply operation
        operator(receiver, **copy)
