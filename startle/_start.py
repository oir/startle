import sys
from typing import Callable, TypeVar

from rich.console import Console

from .args import Args
from .cmds import Cmds
from .error import ParserConfigError, ParserOptionError, ParserValueError
from .inspect import make_args

T = TypeVar("T")


def start(
    obj: Callable | list[Callable] | dict[str, Callable],
    args: list[str] | None = None,
    caught: bool = True,
):
    if isinstance(obj, list) or isinstance(obj, dict):
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
            console.print(f"[bold red]Error:[/bold red] [red]{e}[/red]")
            args_.print_help(console, usage_only=True)
            console.print(
                "[dim]For more information, run with [green][b]-?[/b]|[b]--help[/b][/green].[/dim]\n"
            )
            raise SystemExit(1)
        else:
            raise e


def _start_cmds(
    funcs: list[Callable] | dict[str, Callable],
    cli_args: list[str] | None = None,
    caught: bool = True,
):
    """
    Given a list or dict of functions, parse the command from the CLI and call it.

    Args:
        funcs: The functions to parse the arguments for and invoke.
        cli_args: The arguments to parse. If None, uses the arguments from the CLI.
        caught: Whether to catch and print errors instead of raising.
    """

    if isinstance(funcs, dict):
        cmd2func = funcs
    else:

        def cmd_name(func: Callable) -> str:
            return func.__name__.replace("_", "-")

        cmd2func: dict[str, Callable] = {cmd_name(func): func for func in funcs}

    def prog_name(cmd_name: str) -> str:
        return f"{sys.argv[0]} {cmd_name}"

    try:
        # first, make Cmds object from the functions
        cmds = Cmds(
            {
                cmd_name: make_args(func, program_name=prog_name(cmd_name))
                for cmd_name, func in cmd2func.items()
            }
        )
    except ParserConfigError as e:
        if caught:
            console = Console()
            console.print(f"[bold red]Error:[/bold red] [red]{e}[/red]\n")
            raise SystemExit(1)
        else:
            raise e

    try:
        # then, parse the arguments from the CLI
        args: Args | None = None
        cmd, args, remaining = cmds.get_cmd_parser(cli_args)
        args.parse(remaining)

        # then turn the parsed arguments into function arguments
        f_args, f_kwargs = args.make_func_args()

        # finally, call the function with the arguments
        func = cmd2func[cmd]
        return func(*f_args, **f_kwargs)
    except (ParserOptionError, ParserValueError) as e:
        if caught:
            console = Console()
            console.print(f"[bold red]Error:[/bold red] [red]{e}[/red]")
            if args:  # error happened after parsing the command
                args.print_help(console, usage_only=True)
                console.print(
                    "[dim]For more information, run with [green][b]-?[/b]|[b]--help[/b][/green].[/dim]\n"
                )
            else:  # error happened before parsing the command
                cmds.print_help(console)
            raise SystemExit(1)
        else:
            raise e
