from typing import Callable

from rich.console import Console

from startle._inspect.make_args import make_args_from_class, make_args_from_func

VS = "blue"
NS = "bold"
OS = "green"
TS = "bold underline dim"


def remove_trailing_spaces(text: str) -> str:
    lines = text.split("\n")
    return "\n".join(line.rstrip() for line in lines)


def check_help_from_func(
    f: Callable, program_name: str, expected: str, recurse: bool = False
):
    console = Console(width=120, highlight=False, force_terminal=True)
    with console.capture() as capture:
        args = make_args_from_func(f, program_name=program_name, recurse=recurse)
        args.print_help(console)
    result = capture.get()

    console = Console(width=120, highlight=False, force_terminal=True)
    with console.capture() as capture:
        console.print(expected)
    expected = capture.get()

    assert remove_trailing_spaces(result) == remove_trailing_spaces(expected)


def check_help_from_class(cls: type, brief: str, program_name: str, expected: str):
    console = Console(width=120, highlight=False, force_terminal=True)
    with console.capture() as capture:
        make_args_from_class(cls, program_name=program_name, brief=brief).print_help(
            console
        )
    result = capture.get()

    console = Console(width=120, highlight=False, force_terminal=True)
    with console.capture() as capture:
        console.print(expected)
    expected = capture.get()

    assert remove_trailing_spaces(result) == remove_trailing_spaces(expected)
