import sys
from typing import Callable, TypeVar

from rich.console import Console

from .args import Args
from .cmds import Cmds
from .error import ParserConfigError, ParserOptionError, ParserValueError
from .inspect import make_args

T = TypeVar("T")


def start(
    obj: Callable | list[Callable], args: list[str] | None = None, caught: bool = True
):
    if isinstance(obj, list):
        return _start_cmds(obj, args, caught)
    else:
        return _start_func(obj, args, caught)


def _start_func(
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


def _start_cmds(
    funcs: list[Callable], cli_args: list[str] | None = None, caught: bool = True
):
    """ """

    def cmd_name(func: Callable[..., T]) -> str:
        return func.__name__.replace("_", "-")

    cmd2func: dict[str, Callable] = {cmd_name(func): func for func in funcs}

    try:
        # first, make Cmds object from the functions
        args = {}
        for func in funcs:
            cmd = cmd_name(func)
            arg = make_args(func, program_name=f"{sys.argv[0]} {cmd}")
            args[cmd] = arg
        cmds = Cmds(args)
    except ParserConfigError as e:
        if caught:
            console = Console()
            console.print(f"[bold red]Error:[/bold red] [red]{e}[/red]\n")
            raise SystemExit(1)
        else:
            raise e

    try:
        # then, parse the arguments from the CLI
        cmd: str | None = None
        args: Args | None = None
        cmd, args = cmds.parse(cli_args)

        # then turn the parsed arguments into function arguments
        f_args, f_kwargs = args.make_func_args()

        # finally, call the function with the arguments
        func = cmd2func[cmd]
        return func(*f_args, **f_kwargs)
    except (ParserOptionError, ParserValueError) as e:
        if caught:
            console = Console()
            console.print(f"[bold red]Error:[/bold red] [red]{e}[/red]\n")
            if args:  # error happened after parsing the command
                args.print_help(console, usage_only=True)
            else:  # error happened before parsing the command
                cmds.print_help(console, usage_only=True)
            console.print(
                "\n[dim]For more information, run with [green][b]-?[/b]|[b]--help[/b][/green].[/dim]"
            )
            raise SystemExit(1)
        else:
            raise e
