from mongoengine.base import BaseDocument, EmbeddedDocumentList

class Registry:

    def __init__(self):
        self.lookup = {}
    
    def register(self, name, supports=None, args=None):
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
                for arg, arg_type in args.items():
                    if arg not in kwargs:
                        raise TypeError(f'Missing required arg \'{arg}\'')
                    if arg_type and not isinstance(kwargs[arg], arg_type):
                        raise TypeError(f'Argument \'{arg}\' must be of type \'{arg_type.__name__}\'')
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

@operators.register('set', supports=(BaseDocument, ), args={'field': str, 'value': None})
def set(receiver: BaseDocument, field=None, value=None):
    """
    Sets a field of a document to a value
    """
    receiver[field] = value

@operators.register('create', supports=(EmbeddedDocumentList, ), args={'data': None})
def create(receiver: EmbeddedDocumentList, data=None):
    """
    Inserts a new document into an embedded document list
    """
    receiver.create(**data)

@operators.register('delete', supports=(EmbeddedDocumentList, ), args={'where': dict})
def delete(receiver: EmbeddedDocumentList, where=None):
    """
    Deletes documents that meet certain conditions from an embedded document list
    """
    receiver.filter(**where).delete()

@operators.register('add', supports=(list, ), args={'value': None})
def add(receiver: list, value=None):
    """
    Adds a value to a list
    """
    receiver.append(value)

@operators.register('remove', supports=(list, ), args={'value': None})
def remove(receiver: list, value=None):
    """
    Removes a value from a list
    """
    receiver.remove(value)

class DocumentTransform:
    """
    Describes a way a Mongoengine document can be modified
    'operator' is a function that takes a receiver and arguments, and modifies
    the receiver using the arguments
    'path' is a DocumentPath that can be used to target a specific object inside
    the document
    'args' are the arguments provided to the operator
    """

    def __init__(self, operator, path, args):
        self.operator = operator
        self.path = path
        self.args = args

    def apply(self, document):
        # Resolve path to determine operation receiver
        receiver = self.path.evaluate(document)
        self.operator(receiver, **self.args)