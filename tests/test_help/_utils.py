from typing import Callable

from rich.console import Console

from startle.inspect import make_args_from_func

VS = "blue"
NS = "bold"
OS = "green"
TS = "bold underline dim"


def check_help(f: Callable, program_name: str, expected: str):
    console = Console(width=120, highlight=False, force_terminal=True)
    with console.capture() as capture:
        make_args_from_func(f, program_name).print_help(console)
    result = capture.get()

    console = Console(width=120, highlight=False, force_terminal=True)
    with console.capture() as capture:
        console.print(expected)
    expected = capture.get()

    assert result == expected
