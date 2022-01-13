from mongoengine.base import BaseDocument, EmbeddedDocumentList

class Registry:

    def __init__(self):
        self.lookup = {}
    
    def register(self, name, supported_types=None, required_args=None):
        """
        Registers new functions as operators by decorating them
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
            self.lookup[name] = wrapped
            return wrapped
        return wrapper

    def get(self, name):
        """
        Returns registry entry corresponding to 'name', or None
        """
        return self.lookup.get(name, None)

operators = Registry()

@operators.register('set', supported_types=(BaseDocument, ), required_args=('field', 'value'))
def set(receiver: BaseDocument, field=None, value=None):
    """
    Sets a field of a document to a value
    """
    receiver[field] = value

@operators.register('create', supported_types=(EmbeddedDocumentList, ), required_args=('data', ))
def create(receiver: EmbeddedDocumentList, data=None):
    """
    Inserts a new document into an embedded document list
    """
    receiver.create(**data)

@operators.register('delete', supported_types=(EmbeddedDocumentList, ), required_args=('where', ))
def delete(receiver: EmbeddedDocumentList, where=None):
    """
    Deletes documents that meet certain conditions from an embedded document list
    """
    receiver.filter(**where).delete()

@operators.register('add', supported_types=(list, ), required_args=('value', ))
def add(receiver: list, value=None):
    """
    Adds a value to a list
    """
    receiver.append(value)

@operators.register('remove', supported_types=(list, ), required_args=('value', ))
def remove(receiver: list, value=None):
    """
    Removes a value from a list
    """
    receiver.remove(value)

class DocumentTransform:

    def __init__(self, operator, path, args):
        self.operator = operator
        self.path = path
        self.args = args

    def apply(self, document):
        # Resolve path to determine operation receiver
        receiver = self.path.evaluate(document)
        self.operator(receiver, **self.args)