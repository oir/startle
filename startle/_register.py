from collections.abc import Callable
from typing import Any

from ._type_utils import normalize_type


def register(
    type_: Any,
    parser: Callable[[str], Any] | None = None,
    metavar: str | list[str] | None = None,
) -> None:
    """
    Register a custom parser and metavar for a type.
    `parser` can be omitted to specify a custom metavar for an already parsable type.

    Args:
        type_: The type or annotation to register the parser and metavar for.
        parser: A function that takes a string and returns a value of the type.
        metavar: The metavar to use for the type in the help message.
            If None, default metavar "val" is used.
            If list, the metavar is treated as a literal list of possible choices,
            such as ["true", "false"] yielding "true|false" for a boolean type.
    """
    # TODO: should overwrite be disallowed?

    from ._metavar import METAVARS
    from ._value_parser import PARSERS

    type_ = normalize_type(type_)

    if parser:
        PARSERS[type_] = parser
    if metavar:
        METAVARS[type_] = metavar
