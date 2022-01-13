import re

break_pattern = re.compile(r'(?<!^)(?=[A-Z])')

def snakecase(string):
    return break_pattern.sub('_', string).lower()