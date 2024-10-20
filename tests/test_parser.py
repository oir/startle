from typing import Any, Callable

from pytest import mark, raises

from startle.error import ParserConfigError, ParserOptionError, ParserValueError
from startle.inspector import make_args


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


def test_args_with_defaults():
    def hi_int(name: str = "john", /, *, count: int = 1) -> None:
        for _ in range(count):
            print(f"hello, {name}!")

    def hi_float(name: str = "john", /, *, count: float = 1.0) -> None:
        for _ in range(int(count)):
            print(f"hello, {name}!")

    for hi, count_t in [(hi_int, int), (hi_float, float)]:
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
    def hi(person_name: str, hello_count: int) -> None:
        for _ in range(hello_count):
            print(f"hello, {person_name}!")

    check_args(hi, ["jane", "3"], [], {"person_name": "jane", "hello_count": 3})
    check_args(
        hi,
        ["jane", "--hello-count", "3"],
        [],
        {"person_name": "jane", "hello_count": 3},
    )
    check_args(
        hi,
        ["--person-name", "jane", "--hello-count", "3"],
        [],
        {"person_name": "jane", "hello_count": 3},
    )
    check_args(
        hi,
        ["--hello-count", "3", "--person-name", "jane"],
        [],
        {"person_name": "jane", "hello_count": 3},
    )
    check_args(
        hi,
        ["--person-name", "jane", "3"],
        [],
        {"person_name": "jane", "hello_count": 3},
    )

    with raises(ParserOptionError, match="Option `person-name` is multiply given!"):
        check_args(hi, ["jane", "--person-name", "john", "--hello-count", "3"], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `4`!"):
        check_args(hi, ["jane", "--hello-count", "3", "4"], [], {})


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


@mark.parametrize("short", [False, True])
def test_keyword_nargs(short: bool):
    def add_int(*, numbers: list[int]) -> None:
        print(sum(numbers))

    def add_float(*, numbers: list[float]) -> None:
        print(sum(numbers))

    def add_str(*, numbers: list[str]) -> None:
        print(" ".join(numbers))

    for add, scalar in [(add_int, int), (add_float, float), (add_str, str)]:
        opt = "-n" if short else "--numbers"
        cli = [opt, "0", "1", "2", "3", "4"]
        check_args(add, cli, [], {"numbers": [scalar(i) for i in range(5)]})

        with raises(
            ParserOptionError, match="Required option `numbers` is not provided!"
        ):
            check_args(add, [], [], {})
        with raises(ParserOptionError, match="Option `numbers` is multiply given!"):
            check_args(add, ["--numbers", "0", "1", "-n", "2"], [], {})

        if scalar in [int, float]:
            with raises(
                ParserValueError,
                match=f"Cannot parse {'integer' if scalar is int else 'float'} from `x`!",
            ):
                check_args(add, [opt, "0", "1", "x"], [], {})


@mark.parametrize("short", [False, True])
def test_keyword_nargs_long(short: bool):
    def add1(*, widths: list[int], heights: list[float] = []) -> None:
        print(sum(widths))
        print(sum(heights))

    def add2(*, widths: list[float], heights: list[str] = []) -> None:
        print(sum(widths))
        print(sum(heights))

    def add3(*, widths: list[str], heights: list[int] = []) -> None:
        print(" ".join(widths))
        print(sum(heights))

    for add, scalar, scalar2 in [
        (add1, int, float),
        (add2, float, str),
        (add3, str, int),
    ]:
        wopt = "-w" if short else "--widths"
        hopt = "--heights"
        cli = [wopt, "0", "1", "2", "3", "4", hopt, "5", "6", "7", "8", "9"]
        check_args(
            add,
            cli,
            [],
            {
                "widths": [scalar(i) for i in range(5)],
                "heights": [scalar2(i) for i in range(5, 10)],
            },
        )

        with raises(
            ParserOptionError, match="Required option `widths` is not provided!"
        ):
            check_args(add, [], [], {})
        with raises(
            ParserOptionError, match="Required option `widths` is not provided!"
        ):
            check_args(add, [hopt, "0", "1"], [], {})

        cli = [wopt, "0", "1", "2", "3", "4"]
        check_args(
            add, cli, [], {"widths": [scalar(i) for i in range(5)], "heights": []}
        )

        with raises(
            ParserOptionError, match=f"Option `{hopt.lstrip('-')}` is missing argument!"
        ):
            check_args(add, cli + [hopt], [], {})

        if scalar in [int, float]:
            with raises(
                ParserValueError,
                match=f"Cannot parse {'integer' if scalar is int else 'float'} from `x`!",
            ):
                check_args(add, [wopt, "0", "1", "x"], [], {})
        if scalar2 in [int, float]:
            with raises(
                ParserValueError,
                match=f"Cannot parse {'integer' if scalar2 is int else 'float'} from `x`!",
            ):
                check_args(add, [wopt, "0", "1", hopt, "0", "1", "x"], [], {})


def test_positional_nargs():
    def add_int(numbers: list[int], /) -> None:
        print(sum(numbers))

    def add_float(numbers: list[float], /) -> None:
        print(sum(numbers))

    def add_str(numbers: list[str], /) -> None:
        print(" ".join(numbers))

    for add, scalar in [(add_int, int), (add_float, float), (add_str, str)]:
        cli = ["0", "1", "2", "3", "4"]
        check_args(add, cli, [[scalar(i) for i in range(5)]], {})

        with raises(ParserOptionError, match="Unexpected option `numbers`!"):
            check_args(add, ["--numbers", "0", "1", "2", "3", "4"], [], {})
        with raises(
            ParserOptionError,
            match="Required positional argument <numbers> is not provided!",
        ):
            check_args(add, [], [], {})

        if scalar in [int, float]:
            with raises(
                ParserValueError,
                match=f"Cannot parse {'integer' if scalar is int else 'float'} from `x`!",
            ):
                check_args(add, ["0", "1", "x"], [], {})


def test_positional_nargs_with_defaults():
    def add_int(numbers: list[int] = [3, 5], /) -> None:
        print(sum(numbers))

    def add_float(numbers: list[float] = [3.0, 5.0], /) -> None:
        print(sum(numbers))

    def add_str(numbers: list[str] = ["3", "5"], /) -> None:
        print(" ".join(numbers))

    for add, scalar in [(add_int, int), (add_float, float), (add_str, str)]:
        cli = ["0", "1", "2", "3", "4"]
        check_args(add, cli, [[scalar(i) for i in range(5)]], {})
        check_args(add, [], [[scalar(3), scalar(5)]], {})


def test_positional_nargs_infeasible():
    """
    Below case is ambiguous, because the parser cannot determine the end of the first positional argument.
    TODO: Should there be a `--`-like split? Should we raise an error earlier?
    """

    def rectangle_int(widths: list[int], heights: list[int], /) -> None:
        print(sum(widths))
        print(sum(heights))

    def rectangle_float(widths: list[float], heights: list[float], /) -> None:
        print(sum(widths))
        print(sum(heights))

    def rectangle_str(widths: list[str], heights: list[str], /) -> None:
        print(" ".join(widths))
        print(" ".join(heights))

    for rectangle in [rectangle_int, rectangle_float, rectangle_str]:
        cli = ["0", "1", "2", "3", "4", "5", "6"]
        with raises(
            ParserOptionError,
            match="Required positional argument <heights> is not provided!",
        ):
            check_args(rectangle, cli, [], {})

    """
    This one is oddly feasible 😅
    """

    def rectangle(widths: list[int], heights: list[float], /, verbose: bool) -> None:
        if verbose:
            print(sum(widths))
            print(sum(heights))

    cli = ["0", "1", "2", "3", "4", "-v", "yes", "5.", "6."]
    check_args(
        rectangle,
        cli,
        [list(range(5)), [5.0, 6.0]],
        {"verbose": True},
    )


def test_pathlib_path():
    from pathlib import Path

    def transfer(destination: Path, source: Path = Path("./")) -> None:
        print(f"Transferring from {source} to {destination}.")

    check_args(
        transfer,
        ["./destination", "./source"],
        [],
        {"destination": Path("./destination"), "source": Path("./source")},
    )
    check_args(
        transfer,
        ["./destination"],
        [],
        {"destination": Path("./destination"), "source": Path("./")},
    )
    check_args(
        transfer,
        ["./destination", "--source", "./source"],
        [],
        {"destination": Path("./destination"), "source": Path("./source")},
    )
    check_args(
        transfer,
        ["--source", "./source", "./destination"],
        [],
        {"destination": Path("./destination"), "source": Path("./source")},
    )
    check_args(
        transfer,
        ["--source", "./source", "--destination", "./destination"],
        [],
        {"destination": Path("./destination"), "source": Path("./source")},
    )

    with raises(
        ParserOptionError,
        match="Required positional argument <destination> is not provided!",
    ):
        check_args(transfer, [], [], {})
    with raises(ParserOptionError, match="Option `destination` is missing argument!"):
        check_args(transfer, ["--destination"], [], {})
    with raises(ParserOptionError, match="Option `destination` is multiply given!"):
        check_args(
            transfer, ["./destination", "--destination", "./destination"], [], {}
        )


def test_param_named_help():
    def hi(help: str = "help", count: int = 3) -> None:
        print(f"{help}!")

    def hi2(h: str = "help", count: int = 3) -> None:
        print(f"{h}!")

    with raises(
        ParserConfigError, match="Cannot use `h` or `help` as parameter names in hi!"
    ):
        make_args(hi)
    with raises(
        ParserConfigError, match="Cannot use `h` or `help` as parameter names in hi2!"
    ):
        make_args(hi2)
