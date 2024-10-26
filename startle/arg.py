import typing
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .error import ParserConfigError, ParserValueError


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
    if issubclass(type_, Enum):
        return "|".join([member.value for member in type_])
    return default_metavars.get(type_, "val")


@dataclass
class ValueParser:
    value: str

    def to_builtins__str(self) -> str:
        return self.value

    def to_builtins__int(self) -> int:
        try:
            return int(self.value)
        except ValueError as err:
            raise ParserValueError(
                f"Cannot parse integer from `{self.value}`!"
            ) from err

    def to_builtins__float(self) -> float:
        try:
            return float(self.value)
        except ValueError as err:
            raise ParserValueError(f"Cannot parse float from `{self.value}`!") from err

    def to_builtins__bool(self) -> bool:
        if self.value.lower() in {"true", "t", "yes", "y", "1"}:
            return True
        if self.value.lower() in {"false", "f", "no", "n", "0"}:
            return False
        raise ParserValueError(f"Cannot parse boolean from `{self.value}`!")

    def to_pathlib__Path(self) -> Path:
        return Path(self.value)

    def _to_enum(self, type_: type) -> Enum:
        try:
            return type_(self.value)
        except ValueError as err:
            raise ParserValueError(
                f"Cannot parse enum {type_.__name__} from `{self.value}`!"
            ) from err

    def convert(self, type_: type) -> Any:
        # if type is Optional[T], convert to T
        type_ = _strip_optional(type_)

        # check if type_ is an Enum
        if issubclass(type_, Enum):
            return self._to_enum(type_)

        # check if a method named `to_<fully qualified name>` exists
        method_name = f"to_{type_.__module__}__{type_.__qualname__}"
        if hasattr(self, method_name):
            return getattr(self, method_name)()

        # otherwise it is unsupported
        raise ParserValueError(
            f"Unsupported type {type_.__module__}.{type_.__qualname__}!"
        )


@dataclass
class Name:
    short: str = ""
    long: str = ""

    @property
    def long_or_short(self) -> str:
        return self.long or self.short

    def __str__(self) -> str:
        return self.long_or_short


@dataclass
class Arg:
    """
    Represents a command-line argument.

    Attributes:
        type_ (type): The type of the argument. For n-ary options, this is the type of the list elements.
        help (str): The help text for the argument.
        metavar (str): The name to use in help messages for the argument in place of the value that is fed.
        default (Any): The default value for the argument.
        required (bool): Whether the argument is required.
        name (Name): The name of the argument.
        is_positional (bool): Whether the argument is positional.
        is_named (bool): Whether the argument is named.
        is_nary (bool): Whether the argument can take multiple values.
        _parsed (bool): Whether the argument has been parsed.
        _value (Any): The parsed value of the argument.
    """

    # Note: an Arg can be both positional and named.
    name: Name
    type_: type  # for n-ary options, this is the type of the list elements

    is_positional: bool = False
    is_named: bool = False
    is_nary: bool = False

    help: str = ""
    metavar: str = ""
    default: Any = None
    required: bool = False

    _parsed: bool = False  # if this is already parsed
    _value: Any = None  # the parsed value

    @property
    def is_flag(self) -> bool:
        return self.type_ is bool and self.default is False and not self.is_positional

    def __post_init__(self):
        if not self.is_positional and not self.is_named:
            raise ParserConfigError(
                "An argument should be either positional or named (or both)!"
            )
        if not self.metavar:
            self.metavar = _get_metavar(self.type_)

    def parse(self, value: str | None = None):
        if self.is_flag:
            assert value is None, "Flag options should not have values!"
            self._value = True
            self._parsed = True
        elif self.is_nary:
            assert value is not None, "N-ary options should have values!"
            assert self._value is None or isinstance(
                self._value, list
            ), "Programming error!"
            if self._value is None:
                self._value = []
            self._value.append(ValueParser(value).convert(self.type_))
            self._parsed = True
        else:
            assert value is not None, "Non-flag options should have values!"
            self._value = ValueParser(value).convert(self.type_)
            self._parsed = True
