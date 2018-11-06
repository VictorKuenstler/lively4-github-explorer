import re


_camel_to_snake_regex_1 = re.compile('(.)([A-Z][a-z]+)')
_camel_to_snake_regex_2 = re.compile('([a-z0-9])([A-Z])')


def camel_to_snake(text):
    text = _camel_to_snake_regex_1.sub(r'\1_\2', text)
    return _camel_to_snake_regex_2.sub(r'\1_\2', text).lower()


def snake_to_camel(text):
    return ''.join([w.capitalize() for w in text.split('_')])
