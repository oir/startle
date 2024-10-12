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
    with raises(ParserOptionError, match="Required option `count` is not provided!"):
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


@mark.parametrize("scalar", [int, float, str])
@mark.parametrize("scalar2", [int, float, str])
@mark.parametrize("short", [False, True])
@mark.parametrize("short2", [False, True])
def test_keyword_nargs(scalar: type, scalar2: type, short: bool, short2: bool):
    def add(*, numbers: list[scalar]) -> None:
        print(sum(numbers))

    opt = "-n" if short else "--numbers"
    cli = [opt, "0", "1", "2", "3", "4"]
    check_args(add, cli, [], {"numbers": [scalar(i) for i in range(5)]})

    with raises(ParserOptionError, match="Required option `numbers` is not provided!"):
        check_args(add, [], [], {})
    with raises(ParserOptionError, match="Option `numbers` is multiply given!"):
        check_args(add, ["--numbers", "0", "1", "-n", "2"], [], {})

    if scalar in [int, float]:
        with raises(ParserValueError, match=f"Cannot parse {'integer' if scalar == int else 'float'} from `x`!"):
            check_args(add, [opt, "0", "1", "x"], [], {})
    

    def add2(*, widths: list[scalar], heights: list[scalar2] = []) -> None:
        print(sum(widths))
        print(sum(heights))
    
    wopt = "-w" if short else "--widths"
    hopt = "-h" if short2 else "--heights"
    cli = [wopt, "0", "1", "2", "3", "4", hopt, "5", "6", "7", "8", "9"]
    check_args(add2, cli, [], {"widths": [scalar(i) for i in range(5)], "heights": [scalar2(i) for i in range(5, 10)]})

    with raises(ParserOptionError, match=f"Required option `widths` is not provided!"):
        check_args(add2, [], [], {})
    with raises(ParserOptionError, match=f"Required option `widths` is not provided!"):
        check_args(add2, [hopt, "0", "1"], [], {})

    cli = [wopt, "0", "1", "2", "3", "4"]
    check_args(add2, cli, [], {"widths": [scalar(i) for i in range(5)], "heights": []})

    with raises(ParserOptionError, match=f"Option `{hopt.lstrip('-')}` is missing argument!"):
        check_args(add2, cli + [hopt], [], {})
    
    if scalar in [int, float]:
        with raises(ParserValueError, match=f"Cannot parse {'integer' if scalar == int else 'float'} from `x`!"):
            check_args(add2, [wopt, "0", "1", "x"], [], {})
    if scalar2 in [int, float]:
        with raises(ParserValueError, match=f"Cannot parse {'integer' if scalar2 == int else 'float'} from `x`!"):
            check_args(add2, [wopt, "0", "1", hopt, "0", "1", "x"], [], {})
    

@mark.parametrize("scalar", [int, float, str])
def test_positional_nargs(scalar: type):
    def add(numbers: list[scalar], /) -> None:
        print(sum(numbers))

    cli = ["0", "1", "2", "3", "4"]
    check_args(add, cli, [[scalar(i) for i in range(5)]], {})

    with raises(ParserOptionError, match="Unexpected option `numbers`!"):
        check_args(add, ["--numbers", "0", "1", "2", "3", "4"], [], {})
    with raises(ParserOptionError, match="Required positional argument <numbers> is not provided!"):
        check_args(add, [], [], {})
    
    if scalar in [int, float]:
        with raises(ParserValueError, match=f"Cannot parse {'integer' if scalar == int else 'float'} from `x`!"):
            check_args(add, ["0", "1", "x"], [], {})
    
    def add2(numbers: list[scalar] = [scalar(3), scalar(5)], /) -> None:
        print(sum(numbers))
    
    check_args(add2, cli, [[scalar(i) for i in range(5)]], {})
    check_args(add2, [], [[scalar(3), scalar(5)]], {})

@mark.parametrize("scalar", [int, float, str])
def test_positional_nargs_infeasible(scalar: type):
    """
    Below case is ambiguous, because the parser cannot determine the end of the first positional argument.
    TODO: Should there be a `--`-like split? Should we raise an error earlier?
    """
    def rectangle(widths: list[scalar], heights: list[scalar], /) -> None:
        print(sum(widths))
        print(sum(heights))
    
    cli = ["0", "1", "2", "3", "4", "5", "6"]
    with raises(ParserOptionError, match="Required positional argument <heights> is not provided!"):
        check_args(rectangle, cli, [], {})
    
    """
    This one is oddly feasible 😅
    """
    def rectangle(widths: list[scalar], heights: list[scalar], /, verbose: bool) -> None:
        if verbose:
            print(sum(widths))
            print(sum(heights))
    cli = ["0", "1", "2", "3", "4", "-v", "yes", "5", "6"]
    check_args(rectangle, cli, [[scalar(i) for i in range(5)], [scalar(i) for i in range(5, 7)]], {"verbose": True})
