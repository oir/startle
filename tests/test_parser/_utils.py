from typing import Any, Callable

from startle.inspect import make_args


def check_args(
    f: Callable,
    cli_args: list[str],
    expected_args: list[str],
    expected_kwargs: dict[str, Any],
):
    """
    Check if the parser can parse the CLI arguments correctly.

    Args:
        f: The function to parse the arguments for.
        cli_args: The CLI arguments to parse.
        expected_args: The expected positional arguments.
        expected_kwargs: The expected keyword arguments
    """
    args, kwargs = make_args(f).parse(cli_args).make_func_args()
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
