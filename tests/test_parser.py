from startle.inspector import make_args
from startle.parser import ParserOptionError, ParserValueError
from typing import Callable, Any

from pytest import raises, mark


def check_args(
    f: Callable,
    cli_args: list[str],
    expected_args: list[str],
    expected_kwargs: dict[str, Any],
):
    args, kwargs = make_args(f).parse(cli_args).make_func_args()
    assert args == expected_args
    assert kwargs == expected_kwargs

    for arg, expected_arg in zip(args, expected_args):
        assert type(arg) == type(expected_arg)

    for key, value in kwargs.items():
        assert type(value) == type(expected_kwargs[key])


@mark.parametrize("count_t", [int, float])
def test_args_with_defaults(count_t: type):
    def hi(name: str = "john", /, *, count: count_t = count_t(1)) -> None:
        for _ in range(count):
            print(f"hello, {name}!")

    typestr = "integer" if count_t is int else "float"

    check_args(hi, [], ["john"], {"count": count_t(1)})
    check_args(hi, ["jane"], ["jane"], {"count": count_t(1)})
    check_args(hi, ["jane", "--count", "3"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["--count", "3", "jane"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["--count", "3"], ["john"], {"count": count_t(3)})

    with raises(ParserValueError, match=f"Cannot parse {typestr} from `x`!"):
        check_args(hi, ["jane", "--count", "x"], [], {})
    with raises(ParserValueError, match=f"Cannot parse {typestr} from `x`!"):
        check_args(hi, ["--count", "x", "jane"], [], {})

    with raises(ParserOptionError, match="Unexpected positional argument: `3`!"):
        check_args(hi, ["john", "3"], [], {})

    with raises(ParserOptionError, match="Option `count` is missing argument!"):
        check_args(hi, ["--count"], [], {})
    with raises(ParserOptionError, match="Option `count` is missing argument!"):
        check_args(hi, ["jane", "--count"], [], {})

    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["--name", "jane"], [], {})
    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["--name", "jane", "john"], [], {})
    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["john", "--name", "jane"], [], {})

    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["john", "--count", "3", "--count", "4"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["--count", "3", "john", "--count", "4"], [], {})


def test_args_without_defaults():
    def hi(name: str, /, *, count: int) -> None:
        for _ in range(count):
            print(f"hello, {name}!")

    check_args(hi, ["jane", "--count", "3"], ["jane"], {"count": 3})
    check_args(hi, ["--count", "3", "jane"], ["jane"], {"count": 3})

    with raises(
        ParserOptionError, match="Required positional argument <name> is not provided!"
    ):
        check_args(hi, [], [], {})
    with raises(ParserOptionError, match="Required option <count> is not provided!"):
        check_args(hi, ["jane"], [], {})
    with raises(
        ParserOptionError, match="Required positional argument <name> is not provided!"
    ):
        check_args(hi, ["--count", "3"], [], {})

    with raises(ParserOptionError, match="Unexpected positional argument: `jane`!"):
        check_args(hi, ["jane", "jane", "--count", "3"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["jane", "--count", "3", "--count", "4"], [], {})

    with raises(ParserOptionError, match="Unexpected positional argument: `3`!"):
        check_args(hi, ["jane", "3"], [], {})

    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["--name", "jane"], [], {})
    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["jane", "--name", "jane"], [], {})


def test_args_both_positional_and_keyword():
    def hi(name: str, count: int) -> None:
        for _ in range(count):
            print(f"hello, {name}!")

    check_args(hi, ["jane", "3"], [], {"name": "jane", "count": 3})
    check_args(hi, ["jane", "--count", "3"], [], {"name": "jane", "count": 3})
    check_args(hi, ["--name", "jane", "--count", "3"], [], {"name": "jane", "count": 3})
    check_args(hi, ["--count", "3", "--name", "jane"], [], {"name": "jane", "count": 3})
    check_args(hi, ["--name", "jane", "3"], [], {"name": "jane", "count": 3})

    with raises(ParserOptionError, match="Option `name` is multiply given!"):
        check_args(hi, ["jane", "--name", "john", "--count", "3"], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `4`!"):
        check_args(hi, ["jane", "--count", "3", "4"], [], {})


def test_args_both_positional_and_keyword_with_defaults():
    def hi(name: str = "john", count: int = 1) -> None:
        for _ in range(count):
            print(f"hello, {name}!")

    check_args(hi, [], [], {"name": "john", "count": 1})

    check_args(hi, ["jane"], [], {"name": "jane", "count": 1})
    check_args(hi, ["--name", "jane"], [], {"name": "jane", "count": 1})

    check_args(hi, ["jane", "3"], [], {"name": "jane", "count": 3})
    check_args(hi, ["jane", "--count", "3"], [], {"name": "jane", "count": 3})
    check_args(hi, ["--name", "jane", "--count", "3"], [], {"name": "jane", "count": 3})
    check_args(hi, ["--name", "jane", "3"], [], {"name": "jane", "count": 3})
    check_args(hi, ["--count", "3", "--name", "jane"], [], {"name": "jane", "count": 3})
    check_args(hi, ["--count", "3", "jane"], [], {"name": "jane", "count": 3})

    check_args(hi, ["--count", "3"], [], {"name": "john", "count": 3})


def test_flag():
    def hi(name: str, /, *, verbose: bool = False) -> None:
        print(f"hello, {name}!")
        if verbose:
            print("verbose mode")

    check_args(hi, ["jane"], ["jane"], {"verbose": False})
    check_args(hi, ["jane", "--verbose"], ["jane"], {"verbose": True})
    check_args(hi, ["--verbose", "jane"], ["jane"], {"verbose": True})
    with raises(
        ParserOptionError, match="Required positional argument <name> is not provided!"
    ):
        check_args(hi, ["--verbose"], [], {"verbose": True})
    with raises(ParserOptionError, match="Unexpected positional argument: `true`!"):
        check_args(hi, ["jane", "--verbose", "true"], [], {"verbose": False})


@mark.parametrize(
    "true", ["true", "True", "TRUE", "t", "T", "yes", "Yes", "YES", "y", "Y", "1"]
)
@mark.parametrize(
    "false", ["false", "False", "FALSE", "f", "F", "no", "No", "NO", "n", "N", "0"]
)
def test_bool_but_not_flag(true: str, false: str):
    def hi(name: str, /, *, verbose: bool = True) -> None:
        print(f"hello, {name}!")
        if verbose:
            print("verbose mode")

    check_args(hi, ["jane"], ["jane"], {"verbose": True})
    check_args(hi, ["jane", "--verbose", true], ["jane"], {"verbose": True})
    check_args(hi, ["--verbose", true, "jane"], ["jane"], {"verbose": True})
    check_args(hi, ["jane", "--verbose", false], ["jane"], {"verbose": False})
    check_args(hi, ["--verbose", false, "jane"], ["jane"], {"verbose": False})
    with raises(ParserOptionError, match="Option `verbose` is missing argument!"):
        check_args(hi, ["jane", "--verbose"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `yeah`!"):
        check_args(hi, ["jane", "--verbose", "yeah"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `nah`!"):
        check_args(hi, ["--verbose", "nah", "jane"], [], {})

    def hi2(name: str, verbose: bool = False, /) -> None:
        print(f"hello, {name}!")
        if verbose:
            print("verbose mode")

    check_args(hi2, ["jane"], ["jane", False], {})
    check_args(hi2, ["jane", true], ["jane", True], {})
    check_args(hi2, ["jane", false], ["jane", False], {})

    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi2, ["jane", "maybe"], [], {})

    def hi3(name: str, verbose: bool) -> None:
        print(f"hello, {name}!")
        if verbose:
            print("verbose mode")

    check_args(hi3, ["jane", true], [], {"name": "jane", "verbose": True})
    check_args(hi3, ["jane", false], [], {"name": "jane", "verbose": False})
    check_args(hi3, ["--name", "jane", true], [], {"name": "jane", "verbose": True})
    check_args(hi3, ["--name", "jane", false], [], {"name": "jane", "verbose": False})
    check_args(hi3, ["jane", "--verbose", true], [], {"name": "jane", "verbose": True})
    check_args(
        hi3, ["jane", "--verbose", false], [], {"name": "jane", "verbose": False}
    )
    check_args(hi3, ["--verbose", true, "jane"], [], {"name": "jane", "verbose": True})
    check_args(
        hi3, ["--verbose", false, "jane"], [], {"name": "jane", "verbose": False}
    )
    check_args(
        hi3,
        ["--name", "jane", "--verbose", true],
        [],
        {"name": "jane", "verbose": True},
    )
    check_args(
        hi3,
        ["--name", "jane", "--verbose", false],
        [],
        {"name": "jane", "verbose": False},
    )
    check_args(
        hi3,
        ["--verbose", true, "--name", "jane"],
        [],
        {"name": "jane", "verbose": True},
    )
    check_args(
        hi3,
        ["--verbose", false, "--name", "jane"],
        [],
        {"name": "jane", "verbose": False},
    )

    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi3, ["jane", "maybe"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi3, ["jane", "--verbose", "maybe"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi3, ["--verbose", "maybe", "jane"], [], {})
