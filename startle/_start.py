from typing import Callable, TypeVar

from rich.console import Console

from .error import ParserConfigError, ParserOptionError, ParserValueError
from .inspect import make_args

T = TypeVar("T")


def start(
    func: Callable[..., T], args: list[str] | None = None, caught: bool = True
) -> T:
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
        args_.parse(args)
        f_args, f_kwargs = args_.make_func_args()
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
