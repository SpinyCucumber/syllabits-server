from pypeg2 import *

class StringLiteral(str):
    grammar = contiguous('"', re.compile(r'[^"]*'), '"')

class IntLiteral(int):
    grammar = re.compile("[-+]?\d+")

Literal = [StringLiteral, IntLiteral]

class Condition:
    grammar = attr('key', Symbol), '=', attr('value', Literal)

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
    grammar = attr('property', Symbol), attr('selector', optional('[', Selector, ']'))

class Path(List):
    grammar = Level, maybe_some('.', Level)

class DocumentPath:

    def __init__(self, string):
        self.path = parse(string, Path)    

    def evaluate(self, document):
        result = document
        for level in self.path:
            # Look up property
            result = result[level.property.name]
            # If selector is specified, apply selector
            if (level.selector):
                result = level.selector.apply(result)
        return result