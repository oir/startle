"""
String-to-type conversion functions.
"""

import typing
from enum import Enum
from inspect import isclass
from pathlib import Path
from typing import Any, Callable, Literal, cast

from ._type_utils import _strip_optional
from .error import ParserValueError


def _to_str(value: str) -> str:
    return value


def _to_int(value: str) -> int:
    try:
        return int(value)
    except ValueError as err:
        raise ParserValueError(f"Cannot parse integer from `{value}`!") from err


def _to_float(value: str) -> float:
    try:
        return float(value)
    except ValueError as err:
        raise ParserValueError(f"Cannot parse float from `{value}`!") from err


def _to_bool(value: str) -> bool:
    if value.lower() in {"true", "t", "yes", "y", "1"}:
        return True
    if value.lower() in {"false", "f", "no", "n", "0"}:
        return False
    raise ParserValueError(f"Cannot parse boolean from `{value}`!")


def _to_path(value: str) -> Path:
    return Path(value)  # can this raise?


def _to_enum(value: str, enum_type: type) -> Enum:
    try:
        # for StringEnum and (str, Enum) types, use enum value
        # otherwise use the name of the member
        member_type: type = getattr(enum_type, "_member_type_", object)
        if member_type is str or (member_type is object and issubclass(enum_type, str)):
            return cast(Enum, enum_type(value))
        try:
            enum_type_ = cast(type[Enum], enum_type)
            return enum_type_[value.upper().replace("-", "_")]
        except KeyError:
            raise ParserValueError(
                f"Cannot parse enum {enum_type.__name__} from `{value}`!"
            )
    except ValueError as err:
        raise ParserValueError(
            f"Cannot parse enum {enum_type.__name__} from `{value}`!"
        ) from err


_PARSERS: dict[type, Callable[[str], Any]] = {
    str: _to_str,
    int: _to_int,
    float: _to_float,
    bool: _to_bool,
    Path: _to_path,
}


def _get_parser(type_: Any) -> Callable[[str], Any] | None:
    """
    Get the parser function for a given type.
    """

    # if type is Optional[T], convert to T
    type_ = _strip_optional(type_)

    if typing.get_origin(type_) is Literal:
        type_args = typing.get_args(type_)
        if all(isinstance(arg, str) for arg in type_args):

            def parser(value: str) -> str:
                if value in type_args:
                    return value
                raise ParserValueError(
                    f"Cannot parse literal {type_args} from `{value}`!"
                )

            return parser

    # check if type_ is an Enum
    if isclass(type_) and issubclass(type_, Enum):
        return lambda value: _to_enum(value, type_)

    if fp := _PARSERS.get(type_):
        return fp

    return None


def parse(value: str, type_: Any) -> Any:
    """
    Parse or convert a string value to a given type.
    """
    if parser := _get_parser(type_):
        return parser(value)

    # otherwise it is unsupported
    raise ParserValueError(f"Unsupported type {type_.__module__}.{type_.__qualname__}!")


def is_parsable(type_: Any) -> bool:
    """
    Check if a type is parsable (supported).
    """
    return _get_parser(type_) is not None
