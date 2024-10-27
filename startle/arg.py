from dataclasses import dataclass
from typing import Any

from .error import ParserConfigError
from .metavar import _get_metavar
from .value_parser import parse


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
            self._value.append(parse(value, self.type_))
            self._parsed = True
        else:
            assert value is not None, "Non-flag options should have values!"
            self._value = parse(value, self.type_)
            self._parsed = True
