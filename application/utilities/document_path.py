from pypeg2 import *

class StringLiteral(str):
    grammar = word

class IntLiteral(int):
    grammar = re.compile("[-+]?\d+")

class Condition:
    grammar = attr('key', Symbol), '=', attr('value', StringLiteral)

class FilterSelector(List):
    grammar = Condition, maybe_some(',', Condition)

    def apply(self, receiver):
        kwargs = {cond.key.name: cond.value for cond in self}
        return receiver.get(**kwargs)

class IndexSelector:
    grammar = attr('index', IntLiteral)

    def apply(self, receiver):
        return receiver[self.index]

Selector = [FilterSelector, IndexSelector]

class Level:
    grammar = attr('field', Symbol), attr('selector', optional('[', Selector, ']'))

class Path(List):
    grammar = Level, maybe_some('.', Level)

class DocumentPath:
    """
    A "DocumentPath" is a mini-language for querying specific fields on Mongoengine documents.
    The simplest path is a single field name. E.x: 'author'
    Additional fields can be specified by separating fields with '.', like in Python and JS.
    List fields can be indexed using the familiar bracket syntax. E.x. 'lines[0]'
    Additionally, embedded document list fields can be queried using a "filter selector",
    to select an embedded document with a certain field.
    E.x. 'lines[id=61cfdd8dc3f63c7f1a2873b0].text'
    A more complicated example: 'revision.lines[id=61cfdd8dc3f63c7f1a2873b0].key[2]'
    """

    def __init__(self, string):
        self.path = parse(string, Path)    

    def evaluate(self, document):
        result = document
        for level in self.path:
            # Look up field
            result = result[level.field.name]
            # If selector is specified, apply selector
            if (level.selector):
                result = level.selector.apply(result)
        return result