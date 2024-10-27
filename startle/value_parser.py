import typing
from enum import Enum, IntEnum
from inspect import isclass
from pathlib import Path
from typing import Any, Callable, Literal

from .error import ParserValueError


def _strip_optional(type_: type) -> type:
    """
    Strip the Optional type from a type hint. Given T1 | ... | Tn | None,
    return T1 | ... | Tn.
    """
    if typing.get_origin(type_) is typing.Union:
        args = typing.get_args(type_)
        if type(None) in args:
            args = [arg for arg in args if arg is not type(None)]
            if len(args) == 1:
                return args[0]
            else:
                return typing.Union[tuple(args)]

    return type_


def _get_metavar(type_: type) -> str:
    """
    Get the metavar for a type hint.
    """
    default_metavars = {
        int: "int",
        float: "float",
        str: "text",
        bool: "true|false",
        Path: "path",
    }

    type_ = _strip_optional(type_)
    if isclass(type_) and issubclass(type_, IntEnum):
        return "|".join([str(member.value) for member in type_])
    if isclass(type_) and issubclass(type_, Enum):
        return "|".join([member.value for member in type_])
    return default_metavars.get(type_, "val")


# String to type conversion functions


def to_builtins__str(value: str) -> str:
    return value


def to_builtins__int(value: str) -> int:
    try:
        return int(value)
    except ValueError as err:
        raise ParserValueError(f"Cannot parse integer from `{value}`!") from err


def to_builtins__float(value: str) -> float:
    try:
        return float(value)
    except ValueError as err:
        raise ParserValueError(f"Cannot parse float from `{value}`!") from err


def to_builtins__bool(value: str) -> bool:
    if value.lower() in {"true", "t", "yes", "y", "1"}:
        return True
    if value.lower() in {"false", "f", "no", "n", "0"}:
        return False
    raise ParserValueError(f"Cannot parse boolean from `{value}`!")


def to_pathlib__Path(value: str) -> Path:
    return Path(value)  # can this raise?


def to_enum(value: str, enum_type: type) -> Enum:
    try:
        # first convert string to member type, then member type to enum
        # e.g. member type for IntEnum is int
        member_type = enum_type._member_type_
        value = value if member_type is object else member_type(value)
        return enum_type(value)
    except ValueError as err:
        raise ParserValueError(
            f"Cannot parse enum {enum_type.__name__} from `{value}`!"
        ) from err


_PARSERS: dict[type, Callable[[str], Any]] = {
    str: to_builtins__str,
    int: to_builtins__int,
    float: to_builtins__float,
    bool: to_builtins__bool,
    Path: to_pathlib__Path,
}


def get_parser(type_: type) -> Callable[[str], Any] | None:
    """
    Get the parser function for a given type.
    """

    # if type is Optional[T], convert to T
    type_ = _strip_optional(type_)

    if typing.get_origin(type_) is Literal:
        if all(isinstance(arg, str) for arg in type_.__args__):

            def parser(value: str) -> str:
                if value in type_.__args__:
                    return value
                raise ParserValueError(
                    f"Cannot parse literal {type_.__args__} from `{value}`!"
                )

            return parser

    # check if type_ is an Enum
    if isclass(type_) and issubclass(type_, Enum):
        return lambda value: to_enum(value, type_)

    if fp := _PARSERS.get(type_):
        return fp

    return None


def convert(value: str, type_: type) -> Any:
    """
    Parse / convert a string value to a given type.
    """
    if parser := get_parser(type_):
        return parser(value)

    # otherwise it is unsupported
    raise ParserValueError(f"Unsupported type {type_.__module__}.{type_.__qualname__}!")


def is_parsable(type_: type) -> bool:
    """
    Check if a type is parsable (supported).
    """
    return get_parser(type_) is not None
