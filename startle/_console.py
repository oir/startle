from typing import Literal, NoReturn, overload

from rich.console import Console
from rich.style import StyleType
from rich.text import Text

_console: Console | None = None


def console() -> Console:
    """
    Get the lazily initialized console instance.
    """
    global _console
    if _console is None:
        _console = Console(markup=False)
    return _console


def _print(*parts: str | Text | tuple[str, StyleType]) -> None:
    """
    Print the given parts to the console.
    """
    console().print(Text.assemble(*parts))


@overload
def _error(msg: str, *, exit: Literal[True] = True, endl: bool = True) -> NoReturn: ...


@overload
def _error(msg: str, *, exit: Literal[False], endl: bool) -> None: ...


def _error(
    msg: str, *, exit: Literal[True, False] = True, endl: bool = True
) -> None | NoReturn:
    """
    Print an error message to the console.
    Args:
        msg: The error message to print.
        exit: Whether to exit the program after printing the error.
        endl: Whether to print a newline at the end of the message.
    """
    console().print(
        Text.assemble(
            ("Error:", "bold red"),
            " ",
            (msg, "red"),
            "\n" if endl else "",
        )
    )
    if exit:
        raise SystemExit(1)
    return None


@overload
def _post_error(*, exit: Literal[True] = True) -> NoReturn: ...


@overload
def _post_error(*, exit: Literal[False]) -> None: ...


def _post_error(*, exit: Literal[True, False] = True) -> None | NoReturn:
    """
    Print a post-error message to the console.
    """
    _print(
        ("For more information, run with ", "dim"),
        ("-?", "dim green bold"),
        ("|", "dim green"),
        ("--help", "dim green bold"),
        (".", "dim"),
        "\n",
    )
    if exit:
        raise SystemExit(1)
    return None
