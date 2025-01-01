from typing import Any, Callable


def register(
    type_: type,
    parser: Callable[[str], Any] | None = None,
    metavar: str | list[str] | None = None,
) -> None:
    """
    Register a custom parser and metavar for a type.
    """
    # TODO: should overwrite be disallowed?

    from .metavar import _METAVARS
    from .value_parser import _PARSERS

    if parser:
        _PARSERS[type_] = parser
    if metavar:
        _METAVARS[type_] = metavar