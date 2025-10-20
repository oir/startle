from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Sequence

from ._metavar import get_metavar
from ._value_parser import parse
from .error import ParserConfigError

if TYPE_CHECKING:
    from .args import Args


@dataclass
class Name:
    """
    Name of a command-line argument.
    Includes either a short form (e.g., `f`) or a long form (e.g., `file`), or both.
    """

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
        name: The name of the argument.
        type_: The type of the argument. For n-ary options, this is the type of the list elements.
        container_type: The container type for n-ary options.
        is_positional: Whether the argument is positional.
        is_named: Whether the argument is named.
        is_nary: Whether the argument can take multiple values.
        help: The help text for the argument.
        metavar: The name to use in help messages for the argument in place of the value that is fed.
        default: The default value for the argument.
        default_factory: A callable to generate the default value.
            This is _only_ used for the help string, because dataclass initializers
            already handle getting the default value out of these factories.
        required: Whether the argument is required.
        args: Child Args object for parsing this Arg, for structured recursive parsing.
    """

    name: Name
    type_: type  # for n-ary options, this is the type of the list elements
    container_type: type | None = None  # container type for n-ary options

    # Note: an Arg can be both positional and named.
    is_positional: bool = False
    is_named: bool = False
    is_nary: bool = False

    help: str = ""
    metavar: str | list[str] = ""
    default: Any = None
    default_factory: Callable[[], Any] | None = None
    required: bool = False

    args: "Args | None" = None

    _parsed: bool = False  # if this is already parsed
    _value: Any = None  # the parsed value

    @property
    def is_flag(self) -> bool:
        return self.type_ is bool and self.default is False and not self.is_positional

    @property
    def is_parsed(self) -> bool:
        return self._parsed

    @property
    def value(self) -> Any:
        return self._value

    def __post_init__(self):
        if not self.is_positional and not self.is_named:
            raise ParserConfigError(
                "An argument should be either positional or named (or both)!"
            )
        if not self.metavar:
            self.metavar = get_metavar(self.type_)

    def _append(
        self, container: Sequence[Any] | set[Any], value: Any
    ) -> Sequence[Any] | set[Any]:
        assert self.is_nary, "Programming error!"
        assert value is not None, "N-ary options should have values!"
        assert self.container_type is not None, "Programming error!"
        if isinstance(container, list):
            return container + [value]
        elif self.container_type is tuple:
            assert isinstance(container, tuple), "Programming error!"
            return container + (value,)
        elif self.container_type is set:
            assert isinstance(container, set), "Programming error!"
            return container | {value}
        else:
            raise ParserConfigError("Unsupported container type!")

    def parse(self, value: str | None = None):
        """
        Parse the value into the appropriate type and store.
        """
        if self.is_flag:
            assert value is None, "Flag options should not have values!"
            self._value = True
        elif self.is_nary:
            assert value is not None, "Non-flag options should have values!"
            assert self.container_type is not None, "Programming error!"
            if self._value is None:
                self._value = self.container_type()
            self._value = self._append(self._value, parse(value, self.type_))
        else:
            assert value is not None, "Non-flag options should have values!"
            self._value = parse(value, self.type_)
        self._parsed = True
