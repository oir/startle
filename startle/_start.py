from typing import Callable, TypeVar

from rich.console import Console

from .error import ParserConfigError, ParserOptionError, ParserValueError
from .inspect import make_args

T = TypeVar("T")


def start(
    func: Callable[..., T], args: list[str] | None = None, caught: bool = True
) -> T:
    """
    Given a function `func`, parse its arguments from the CLI and call it.

    Args:
        func: The function to parse the arguments for and invoke.
        args: The arguments to parse. If None, uses the arguments from the CLI.
        caught: Whether to catch and print errors instead of raising.
    Returns:
        The return value of the function `func`.
    """
    try:
        # first, make Args object from the function
        args_ = make_args(func)
    except ParserConfigError as e:
        if caught:
            console = Console()
            console.print(f"[bold red]Error:[/bold red] [red]{e}[/red]\n")
            raise SystemExit(1)
        else:
            raise e

    try:
        # then, parse the arguments from the CLI
        args_.parse(args)

        # then turn the parsed arguments into function arguments
        f_args, f_kwargs = args_.make_func_args()

        # finally, call the function with the arguments
        return func(*f_args, **f_kwargs)
    except (ParserOptionError, ParserValueError) as e:
        if caught:
            console = Console()
            console.print(f"[bold red]Error:[/bold red] [red]{e}[/red]\n")
            args_.print_help(console, usage_only=True)
            console.print(
                "\n[dim]For more information, run with [green][b]-?[/b]|[b]--help[/b][/green].[/dim]"
            )
            raise SystemExit(1)
        else:
            raise e
