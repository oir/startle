from collections.abc import Callable
from copy import copy
from types import FunctionType
from typing import Any

from startle._inspect.make_args import make_args_from_func


def check_args(
    f: Callable[..., Any],
    cli_args: list[str],
    expected_args: list[Any],
    expected_kwargs: dict[str, Any],
    recurse: bool = False,
):
    """
    Check if the parser can parse the CLI arguments correctly.

    Args:
        f: The function to parse the arguments for.
        cli_args: The CLI arguments to parse.
        expected_args: The expected positional arguments.
        expected_kwargs: The expected keyword arguments
        recurse: Whether to recursively parse complex types.
    """
    args, kwargs = (
        make_args_from_func(f, recurse=recurse).parse(cli_args).make_func_args()
    )
    assert args == expected_args
    assert kwargs == expected_kwargs

    for arg, expected_arg in zip(args, expected_args):
        assert type(arg) is type(expected_arg)

    for key, value in kwargs.items():
        assert type(value) is type(expected_kwargs[key])


class Opts:
    @staticmethod
    def positional(name: str, value: list[str]) -> list[str]:
        return value

    @staticmethod
    def short(name: str, value: list[str]) -> list[str]:
        return [f"-{name[0]}"] + value

    @staticmethod
    def long(name: str, value: list[str]) -> list[str]:
        return [f"--{name}"] + value

    @staticmethod
    def short_eq(name: str, value: list[str]) -> list[str]:
        return [f"-{name[0]}={item}" for item in value]

    @staticmethod
    def long_eq(name: str, value: list[str]) -> list[str]:
        return [f"--{name}={item}" for item in value]

    # iterate over the different options
    def __iter__(self):
        for name in ["positional", "short", "long", "short_eq", "long_eq"]:
            yield getattr(self, name)


Opt = Callable[[str, list[str]], list[str]]


def copy_function(
    f: Callable[..., Any],
    annotations: dict[str, Any] | None = None,
    defaults: tuple[Any, ...] | None = None,
    kwdefaults: dict[str, Any] | None = None,
) -> Callable[..., Any]:
    new_func = FunctionType(
        f.__code__,
        f.__globals__,
        name=f.__name__,
    )
    new_func.__dict__.update(f.__dict__)
    new_func.__annotations__ = copy(f.__annotations__)
    if annotations:
        new_func.__annotations__.update(annotations)
    new_func.__defaults__ = copy(f.__defaults__) if f.__defaults__ else None
    if defaults:
        new_func.__defaults__ = defaults
    new_func.__kwdefaults__ = copy(f.__kwdefaults__) if f.__kwdefaults__ else None
    if kwdefaults:
        new_func.__kwdefaults__ = kwdefaults
    return new_func
