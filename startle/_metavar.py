import sys
from enum import Enum
from inspect import isclass
from pathlib import Path
from typing import Any, Literal, get_args, get_origin

from ._type_utils import strip_optional

_METAVARS: dict[type, str | list[str]] = {
    int: "int",
    float: "float",
    str: "text",
    bool: ["true", "false"],
    Path: "path",
}


def get_metavar(type_: Any) -> str | list[str]:
    """
    Get the metavar for a type hint.
    If the result is a list, we assume it is a list of possible choices,
    and the options are literally typed in.
    """
    type_ = strip_optional(type_)
    if get_origin(type_) is Literal:
        if all(isinstance(value, str) for value in get_args(type_)):
            return list(get_args(type_))

    if sys.version_info >= (3, 11):
        from enum import StrEnum

        if isclass(type_) and issubclass(type_, StrEnum):
            return [member.value for member in type_]

    if isclass(type_) and issubclass(type_, Enum) and issubclass(type_, str):
        return [member.value for member in type_]

    if isclass(type_) and issubclass(type_, Enum):
        return [member.name.lower().replace("_", "-") for member in type_]

    return _METAVARS.get(type_, "val")
