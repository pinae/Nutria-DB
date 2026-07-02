import re

_NAME_CHARS = r"[\w \-\(\[\{\}\]\)\#\%\!\.\,\;\*]+"
_SPLIT_NAME_RE = re.compile(r"^\s*(" + _NAME_CHARS + r")\s*:\s*(" + _NAME_CHARS + r")\s*$")


def split_name(name_str):
    """Split "Category: name addition" into its two parts.

    Returns (None, name_str) if the string does not contain a category.
    """
    match = _SPLIT_NAME_RE.match(name_str)
    if match is None:
        return None, name_str
    category_str, name_addition = match.groups()
    return category_str, name_addition
