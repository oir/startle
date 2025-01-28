from typing import Type, TypeVar

from rich.console import Console

from .error import ParserConfigError, ParserOptionError, ParserValueError
from .inspect import make_args_from_class

T = TypeVar("T")


def parse(
    cls: Type[T],
    args: list[str] | None = None,
    brief: str = "",
    caught: bool = True,
) -> T:
    """
    Given a class `cls`, parse arguments from the command-line according to the
    class definition and construct an instance.

    Args:
        cls: The class to parse the arguments for and construct an instance of.
        args: The arguments to parse. If None, uses the arguments from the command-line
            (i.e. sys.argv).
        brief: The brief description of the parser. This is used to display a brief
            when --help is invoked.
        caught: Whether to catch and print (startle specific) errors instead of raising.
            This is used to display a more presentable output when a parse error occurs instead
            of the default traceback. This option will never catch non-startle errors.
    Returns:
        An instance of the class `cls`.
    """
    try:
        # first, make Args object from the class
        args_ = make_args_from_class(cls, brief=brief)
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

        # then turn the parsed arguments into function arguments for class initialization
        f_args, f_kwargs = args_.make_func_args()

        # finally, construct an instance of the class
        return cls(*f_args, **f_kwargs)
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
