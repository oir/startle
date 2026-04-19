import sys
from collections.abc import Callable
from inspect import iscoroutinefunction
from typing import Any, Literal, TypeVar, cast

from ._console import console, error, post_error
from ._inspect.make_args import make_args_from_func
from .args import Args
from .cmds import Cmds
from .error import (
    CmdsRecurseError,
    ParserOptionError,
    ParserValueError,
    SingleFunctionDefaultCommandError,
)

T = TypeVar("T")


def start(
    obj: Callable[..., Any] | list[Callable[..., Any]] | dict[str, Callable[..., Any]],
    *,
    name: str | None = None,
    args: list[str] | None = None,
    catch: bool = True,
    default: str | None = None,
    recurse: bool = False,
    naming: Literal["flat", "nested"] = "flat",
) -> Any:
    """
    Given a function, or a container of functions `obj`, parse its arguments from
    the command-line and call it.

    Args:
        obj: The function or functions to parse the arguments for and invoke.
            If a list or dict, the functions are treated as subcommands.
        name: The name of the program. If None, uses the name of the script
            (i.e. sys.argv[0]).
        args: The arguments to parse. If None, uses the arguments from the command-line
            (i.e. sys.argv).
        catch: Whether to catch and print (startle specific) errors instead of raising.
            This is used to display a more presentable output when a parse error occurs instead
            of the default traceback. This option will never catch non-startle errors.
        default: The default subcommand to run if no subcommand is specified immediately
            after the program name. This is only used if `obj` is a list or dict, and
            errors otherwise.
        recurse: (experimental) Whether to recursively parse objects using their initializers.
        naming: How to name nested arguments when `recurse` is True.
            "flat" means all arguments are at the top level with their names (e.g. `--baz`),
            while "nested" means arguments are named using dot notation to indicate
            their nesting (e.g. `--foo.bar.baz`).
            Ignored if `recurse` is False.
    Returns:
        The return value of the function `obj`, or the subcommand of `obj` if it is
        a list or dict.
    """
    if isinstance(obj, list) or isinstance(obj, dict):
        obj = cast(list[Callable[..., Any]] | dict[str, Callable[..., Any]], obj)
        if recurse:
            raise CmdsRecurseError()
        return _start_cmds(obj, name, args, catch, default)
    else:
        if default is not None:
            raise SingleFunctionDefaultCommandError()
        return _start_func(obj, name, args, catch, recurse, naming)


def _start_func(
    func: Callable[..., T],
    name: str | None,
    args: list[str] | None = None,
    catch: bool = True,
    recurse: bool = False,
    naming: Literal["flat", "nested"] = "flat",
) -> T:
    """
    Given a function `func`, parse its arguments from the CLI and call it.

    Args:
        func: The function to parse the arguments for and invoke.
        name: The name of the program. If None, uses the name of the script.
        args: The arguments to parse. If None, uses the arguments from the CLI.
        catch: Whether to catch and print errors instead of raising.
        recurse: (experimental) Whether to recursively parse objects using their initializers.
        naming: How to name nested arguments when `recurse` is True.
            "flat" means all arguments are at the top level with their names (e.g. `--baz`),
            while "nested" means arguments are named using dot notation to indicate
            their nesting (e.g. `--foo.bar.baz`).
            Ignored if `recurse` is False.
    Returns:
        The return value of the function `func`.
    """
    # first, make Args object from the function
    args_ = make_args_from_func(func, name or "", recurse=recurse, naming=naming)

    try:
        # then, parse the arguments from the CLI
        args_.parse(args)

        # then turn the parsed arguments into function arguments
        f_args, f_kwargs = args_.make_func_args()

        # finally, call the function with the arguments
        if iscoroutinefunction(func):
            import asyncio

            return asyncio.run(func(*f_args, **f_kwargs))
        else:
            return func(*f_args, **f_kwargs)
    except (ParserOptionError, ParserValueError) as e:
        if catch:
            error(str(e), exit=False, endl=False)
            args_.print_help(console(), usage_only=True)
            post_error()
        else:
            raise e


def _start_cmds(
    funcs: list[Callable[..., Any]] | dict[str, Callable[..., Any]],
    name: str | None = None,
    cli_args: list[str] | None = None,
    catch: bool = True,
    default: str | None = None,
):
    """
    Given a list or dict of functions, parse the command from the CLI and call it.

    Args:
        funcs: The functions to parse the arguments for and invoke.
        name: The name of the program. If None, uses the name of the script.
        cli_args: The arguments to parse. If None, uses the arguments from the CLI.
        catch: Whether to catch and print errors instead of raising.
        default: The default subcommand to run if no subcommand is specified immediately
            after the program name.
    """

    def _normalize(name: str) -> str:
        return name.replace("_", "-")

    def cmd_prog_name(cmd_name: str) -> str:
        # TODO: more reliable way of getting the program name
        return f"{name or sys.argv[0]} {cmd_name}"

    items: list[tuple[str, Callable[..., Any]]] = (
        list(funcs.items())
        if isinstance(funcs, dict)
        else [(func.__name__, func) for func in funcs]
    )
    cmds = Cmds(
        {
            original: make_args_from_func(func, cmd_prog_name(_normalize(original)))
            for original, func in items
        },
        program_name=name or "",
        default=default or "",
    )

    cmd2func: dict[str, Callable[..., Any]] = {
        _normalize(original): func for original, func in items
    }

    args: Args | None = None
    try:
        # then, parse the arguments from the CLI
        cmd, args, remaining = cmds.get_cmd_parser(cli_args)
        args.parse(remaining)

        # then turn the parsed arguments into function arguments
        f_args, f_kwargs = args.make_func_args()

        # finally, call the function with the arguments
        func = cmd2func[cmd]

        if iscoroutinefunction(func):
            import asyncio

            return asyncio.run(func(*f_args, **f_kwargs))
        else:
            return func(*f_args, **f_kwargs)
    except (ParserOptionError, ParserValueError) as e:
        if catch:
            error(str(e), exit=False, endl=False)
            if args:  # error happened after parsing the command
                args.print_help(console(), usage_only=True)
                post_error(exit=False)
            else:  # error happened before parsing the command
                cmds.print_help(console())
            raise SystemExit(1) from e
        else:
            raise e
