from typing import Callable, List

from _utils import check_args
from pytest import mark, raises

from startle.error import ParserConfigError, ParserOptionError, ParserValueError
from startle.inspector import make_args


def hi_int(name: str = "john", /, *, count: int = 1) -> None:
    for _ in range(count):
        print(f"hello, {name}!")


def hi_float(name: str = "john", /, *, count: float = 1.0) -> None:
    for _ in range(int(count)):
        print(f"hello, {name}!")


@mark.parametrize("hi, count_t", [(hi_int, int), (hi_float, float)])
def test_args_with_defaults(hi, count_t):
    typestr = "integer" if count_t is int else "float"

    check_args(hi, [], ["john"], {"count": count_t(1)})
    check_args(hi, ["jane"], ["jane"], {"count": count_t(1)})
    check_args(hi, ["jane", "--count", "3"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["jane", "--count=3"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["--count", "3", "jane"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["--count", "3"], ["john"], {"count": count_t(3)})
    check_args(hi, ["jane", "-c", "3"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["jane", "-c=3"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["-c", "3", "jane"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["-c", "3"], ["john"], {"count": count_t(3)})

    with raises(ParserValueError, match=f"Cannot parse {typestr} from `x`!"):
        check_args(hi, ["jane", "--count", "x"], [], {})
    with raises(ParserValueError, match=f"Cannot parse {typestr} from `x`!"):
        check_args(hi, ["--count", "x", "jane"], [], {})
    with raises(ParserValueError, match=f"Cannot parse {typestr} from `x`!"):
        check_args(hi, ["jane", "--count=x"], [], {})

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
    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["--name=jane"], [], {})

    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["john", "--count", "3", "--count", "4"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["john", "--count", "3", "-c", "4"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["john", "--count=3", "--count", "4"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["john", "--count", "3", "-count=4"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["--count", "3", "john", "--count", "4"], [], {})


@mark.parametrize("opt", ["-c", "--count"])
def test_args_without_defaults(opt):
    def hi(name: str, /, *, count: int) -> None:
        for _ in range(count):
            print(f"hello, {name}!")

    check_args(hi, ["jane", opt, "3"], ["jane"], {"count": 3})
    check_args(hi, [opt, "3", "jane"], ["jane"], {"count": 3})
    check_args(hi, ["jane", f"{opt}=3"], ["jane"], {"count": 3})
    check_args(hi, [f"{opt}=3", "jane"], ["jane"], {"count": 3})

    with raises(
        ParserOptionError, match="Required positional argument <name> is not provided!"
    ):
        check_args(hi, [], [], {})
    with raises(ParserOptionError, match="Required option `count` is not provided!"):
        check_args(hi, ["jane"], [], {})
    with raises(
        ParserOptionError, match="Required positional argument <name> is not provided!"
    ):
        check_args(hi, [opt, "3"], [], {})

    with raises(ParserOptionError, match="Unexpected positional argument: `jane`!"):
        check_args(hi, ["jane", "jane", opt, "3"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["jane", opt, "3", "-c", "4"], [], {})

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

    check_args(hi, ["jane", "3"], ["jane", 3], {})
    check_args(hi, ["jane", "--hello-count", "3"], ["jane", 3], {})
    check_args(hi, ["--person-name", "jane", "--hello-count", "3"], ["jane", 3], {})
    check_args(hi, ["--hello-count", "3", "--person-name", "jane"], ["jane", 3], {})
    check_args(hi, ["--person-name", "jane", "3"], ["jane", 3], {})

    with raises(ParserOptionError, match="Option `person-name` is multiply given!"):
        check_args(hi, ["jane", "--person-name", "john", "--hello-count", "3"], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `4`!"):
        check_args(hi, ["jane", "--hello-count", "3", "4"], [], {})


def test_args_both_positional_and_keyword_with_defaults():
    def hi(name: str = "john", count: int = 1) -> None:
        for _ in range(count):
            print(f"hello, {name}!")

    check_args(hi, [], ["john", 1], {})

    check_args(hi, ["jane"], ["jane", 1], {})
    check_args(hi, ["--name", "jane"], ["jane", 1], {})

    check_args(hi, ["jane", "3"], ["jane", 3], {})
    check_args(hi, ["jane", "--count", "3"], ["jane", 3], {})
    check_args(hi, ["--name", "jane", "--count", "3"], ["jane", 3], {})
    check_args(hi, ["--name", "jane", "3"], ["jane", 3], {})
    check_args(hi, ["--count", "3", "--name", "jane"], ["jane", 3], {})
    check_args(hi, ["--count", "3", "jane"], ["jane", 3], {})

    check_args(hi, ["--count", "3"], ["john", 3], {})


@mark.parametrize("opt", ["-v", "--verbose"])
def test_flag(opt):
    def hi(name: str, /, *, verbose: bool = False) -> None:
        print(f"hello, {name}!")
        if verbose:
            print("verbose mode")

    check_args(hi, ["jane"], ["jane"], {"verbose": False})
    check_args(hi, ["jane", opt], ["jane"], {"verbose": True})
    check_args(hi, [opt, "jane"], ["jane"], {"verbose": True})
    with raises(
        ParserOptionError, match="Required positional argument <name> is not provided!"
    ):
        check_args(hi, [opt], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `true`!"):
        check_args(hi, ["jane", opt, "true"], [], {})
    with raises(ParserOptionError, match="Option `verbose` is multiply given!"):
        check_args(hi, ["jane", opt, opt], [], {})
    with raises(
        ParserOptionError,
        match="Option `verbose` is a flag and cannot be assigned a value!",
    ):
        check_args(hi, ["jane", f"{opt}=true"], [], {})


@mark.parametrize(
    "true", ["true", "True", "TRUE", "t", "T", "yes", "Yes", "YES", "y", "Y", "1"]
)
@mark.parametrize(
    "false", ["false", "False", "FALSE", "f", "F", "no", "No", "NO", "n", "N", "0"]
)
@mark.parametrize("optv", ["-v", "--verbose"])
@mark.parametrize("optn", ["-n", "--name"])
def test_bool_but_not_flag(true: str, false: str, optv: str, optn: str):
    def hi(name: str, /, *, verbose: bool = True) -> None:
        print(f"hello, {name}!")
        if verbose:
            print("verbose mode")

    check_args(hi, ["jane"], ["jane"], {"verbose": True})
    for verbose in [True, False]:
        value = true if verbose else false
        check_args(hi, ["jane", optv, value], ["jane"], {"verbose": verbose})
        check_args(hi, [optv, value, "jane"], ["jane"], {"verbose": verbose})
        check_args(hi, ["jane", f"{optv}={value}"], ["jane"], {"verbose": verbose})
        check_args(hi, [f"{optv}={value}", "jane"], ["jane"], {"verbose": verbose})
    with raises(ParserOptionError, match="Option `verbose` is missing argument!"):
        check_args(hi, ["jane", optv], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `yeah`!"):
        check_args(hi, ["jane", optv, "yeah"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `yeah`!"):
        check_args(hi, ["jane", f"{optv}=yeah"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `nah`!"):
        check_args(hi, [optv, "nah", "jane"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `nah`!"):
        check_args(hi, [f"{optv}=nah", "jane"], [], {})

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

    for verbose in [True, False]:
        value = true if verbose else false
        check_args(hi3, ["jane", value], ["jane", verbose], {})
        check_args(hi3, [optn, "jane", value], ["jane", verbose], {})
        check_args(hi3, ["jane", optv, value], ["jane", verbose], {})
        check_args(hi3, [optv, value, "jane"], ["jane", verbose], {})
        check_args(hi3, [optn, "jane", optv, value], ["jane", verbose], {})
        check_args(hi3, [optv, value, optn, "jane"], ["jane", verbose], {})

    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi3, ["jane", "maybe"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi3, ["jane", optv, "maybe"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi3, ["jane", f"{optv}=maybe"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi3, [optv, "maybe", "jane"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi3, [f"{optv}=maybe", "jane"], [], {})


def add_int(*, numbers: list[int]) -> None:
    print(sum(numbers))


def add_float(*, numbers: list[float]) -> None:
    print(sum(numbers))


def add_str(*, numbers: list[str]) -> None:
    print(" ".join(numbers))


def add_int2(*, numbers: List[int]) -> None:
    print(sum(numbers))


def add_float2(*, numbers: List[float]) -> None:
    print(sum(numbers))


def add_str2(*, numbers: list[str]) -> None:
    print(" ".join(numbers))


@mark.parametrize(
    "add, scalar",
    [
        (add_int, int),
        (add_float, float),
        (add_str, str),
        (add_int2, int),
        (add_float2, float),
        (add_str2, str),
    ],
)
@mark.parametrize("opt", ["-n", "--numbers"])
def test_keyword_nargs(add: Callable, scalar: type, opt: str) -> None:
    cli = [opt] + [str(i) for i in range(5)]
    check_args(add, cli, [], {"numbers": [scalar(i) for i in range(5)]})
    cli = [f"{opt}={i}" for i in range(5)]
    check_args(add, cli, [], {"numbers": [scalar(i) for i in range(5)]})

    check_args(
        add,
        ["--numbers", "0", "1", "-n", "2"],
        [],
        {"numbers": [scalar(i) for i in range(3)]},
    )

    with raises(ParserOptionError, match="Required option `numbers` is not provided!"):
        check_args(add, [], [], {})

    if scalar in [int, float]:
        with raises(
            ParserValueError,
            match=f"Cannot parse {'integer' if scalar is int else 'float'} from `x`!",
        ):
            check_args(add, [opt, "0", "1", "x"], [], {})


def addwh1(*, widths: list[int], heights: list[float] = []) -> None:
    print(sum(widths))
    print(sum(heights))


def addwh2(*, widths: list[float], heights: list[str] = []) -> None:
    print(sum(widths))
    print(sum(heights))


def addwh3(*, widths: list[str], heights: list[int] = []) -> None:
    print(" ".join(widths))
    print(sum(heights))


@mark.parametrize(
    "add, wscalar, hscalar",
    [
        (addwh1, int, float),
        (addwh2, float, str),
        (addwh3, str, int),
    ],
)
@mark.parametrize("short", [False, True])
def test_keyword_nargs_long(
    add: Callable, wscalar: type, hscalar: type, short: bool
) -> None:
    wopt = "-w" if short else "--widths"
    hopt = "--heights"
    cli = [wopt, "0", "1", "2", "3", "4", hopt, "5", "6", "7", "8", "9"]
    check_args(
        add,
        cli,
        [],
        {
            "widths": [wscalar(i) for i in range(5)],
            "heights": [hscalar(i) for i in range(5, 10)],
        },
    )

    with raises(ParserOptionError, match="Required option `widths` is not provided!"):
        check_args(add, [], [], {})
    with raises(ParserOptionError, match="Required option `widths` is not provided!"):
        check_args(add, [hopt, "0", "1"], [], {})

    cli = [wopt, "0", "1", "2", "3", "4"]
    check_args(add, cli, [], {"widths": [wscalar(i) for i in range(5)], "heights": []})

    with raises(
        ParserOptionError, match=f"Option `{hopt.lstrip('-')}` is missing argument!"
    ):
        check_args(add, cli + [hopt], [], {})

    if wscalar in [int, float]:
        with raises(
            ParserValueError,
            match=f"Cannot parse {'integer' if wscalar is int else 'float'} from `x`!",
        ):
            check_args(add, [wopt, "0", "1", "x"], [], {})
    if hscalar in [int, float]:
        with raises(
            ParserValueError,
            match=f"Cannot parse {'integer' if hscalar is int else 'float'} from `x`!",
        ):
            check_args(add, [wopt, "0", "1", hopt, "0", "1", "x"], [], {})


def add_list_pos_int(numbers: list[int], /) -> None:
    print(sum(numbers))


def add_list_pos_float(numbers: list[float], /) -> None:
    print(sum(numbers))


def add_list_pos_str(numbers: list[str], /) -> None:
    print(" ".join(numbers))


def add_list_pos_int2(numbers: List[int], /) -> None:
    print(sum(numbers))


def add_list_pos_float2(numbers: List[float], /) -> None:
    print(sum(numbers))


def add_list_pos_str2(numbers: List[str], /) -> None:
    print(" ".join(numbers))


def add_list_pos_str3(numbers: list, /) -> None:
    print(" ".join(numbers))


def add_list_pos_str4(numbers: List, /) -> None:
    print(" ".join(numbers))


@mark.parametrize(
    "add, scalar",
    [
        (add_list_pos_int, int),
        (add_list_pos_float, float),
        (add_list_pos_str, str),
        (add_list_pos_int2, int),
        (add_list_pos_float2, float),
        (add_list_pos_str2, str),
        (add_list_pos_str3, str),
        (add_list_pos_str4, str),
    ],
)
def test_positional_nargs(add: Callable, scalar: type) -> None:
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


def posd_add_list_int(numbers: list[int] = [3, 5], /) -> None:
    print(sum(numbers))


def posd_add_list_float(numbers: list[float] = [3.0, 5.0], /) -> None:
    print(sum(numbers))


def posd_add_list_str(numbers: list[str] = ["3", "5"], /) -> None:
    print(" ".join(numbers))


def posd_add_list_int2(numbers: List[int] = [3, 5], /) -> None:
    print(sum(numbers))


def posd_add_list_float2(numbers: List[float] = [3.0, 5.0], /) -> None:
    print(sum(numbers))


def posd_add_list_str2(numbers: List[str] = ["3", "5"], /) -> None:
    print(" ".join(numbers))


def posd_add_list_str3(numbers: list = ["3", "5"], /) -> None:
    print(" ".join(numbers))


def posd_add_list_str4(numbers: List = ["3", "5"], /) -> None:
    print(" ".join(numbers))


@mark.parametrize(
    "add, scalar",
    [
        (posd_add_list_int, int),
        (posd_add_list_float, float),
        (posd_add_list_str, str),
        (posd_add_list_int2, int),
        (posd_add_list_float2, float),
        (posd_add_list_str2, str),
        (posd_add_list_str3, str),
        (posd_add_list_str4, str),
    ],
)
def test_positional_nargs_with_defaults(add: Callable, scalar: type) -> None:
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
        [list(range(5)), [5.0, 6.0], True],
        {},
    )


def test_pathlib_path():
    from pathlib import Path

    def transfer(destination: Path, source: Path = Path("./")) -> None:
        print(f"Transferring from {source} to {destination}.")

    check_args(
        transfer,
        ["./destination", "./source"],
        [Path("./destination"), Path("./source")],
        {},
    )
    check_args(
        transfer,
        ["./destination"],
        [Path("./destination"), Path("./")],
        {},
    )
    check_args(
        transfer,
        ["./destination", "--source", "./source"],
        [Path("./destination"), Path("./source")],
        {},
    )
    check_args(
        transfer,
        ["--source", "./source", "./destination"],
        [Path("./destination"), Path("./source")],
        {},
    )
    check_args(
        transfer,
        ["--source", "./source", "--destination", "./destination"],
        [Path("./destination"), Path("./source")],
        {},
    )

    with raises(
        ParserOptionError,
        match="Required option `destination` is not provided!",
    ):
        check_args(transfer, [], [], {})
    with raises(ParserOptionError, match="Option `destination` is missing argument!"):
        check_args(transfer, ["--destination"], [], {})
    with raises(ParserOptionError, match="Option `destination` is multiply given!"):
        check_args(
            transfer, ["./destination", "--destination", "./destination"], [], {}
        )


def hi_help_1(help: str = "help", count: int = 3) -> None:
    print(f"{help}!")


def hi_help_2(h: str = "help", count: int = 3) -> None:
    print(f"{h}!")


@mark.parametrize("hi", [hi_help_1, hi_help_2])
def test_param_named_help(hi: Callable):
    with raises(
        ParserConfigError,
        match=f"Cannot use `h` or `help` as parameter names in {hi.__name__}!",
    ):
        make_args(hi)
