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