from enum import Enum, IntEnum
from inspect import isclass
from pathlib import Path
from typing import Literal, get_origin

from ._type_utils import _strip_optional

_METAVARS: dict[type, str] = {
    int: "int",
    float: "float",
    str: "text",
    bool: "true|false",
    Path: "path",
}


def _get_metavar(type_: type) -> str:
    """
    Get the metavar for a type hint.
    """
    type_ = _strip_optional(type_)
    if get_origin(type_) is Literal:
        if all(isinstance(value, str) for value in type_.__args__):
            return "|".join(type_.__args__)

    if isclass(type_) and issubclass(type_, IntEnum):
        return "|".join([str(member.value) for member in type_])

    if isclass(type_) and issubclass(type_, Enum):
        return "|".join([member.value for member in type_])

    return _METAVARS.get(type_, "val")
