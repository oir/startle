from typing import Callable, List

from pytest import mark, raises

from startle.error import ParserOptionError, ParserValueError

from ._utils import check_args


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
def test_keyword_list(add: Callable, scalar: type, opt: str) -> None:
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
    print(sum([float(x) for x in heights]))


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

    for rectangle, type_ in [(rectangle_int, int), (rectangle_float, float), (rectangle_str, str)]:
        cli = ["0", "1", "2", "3", "4", "5", "6"]
        with raises(
            ParserOptionError,
            match="Required positional argument <heights> is not provided!",
        ):
            check_args(rectangle, cli, [], {})

        
        # the following works but only once, since "--" has its special meaning only
        # the first time.
        check_args(
            rectangle,
            ["0", "1", "2", "3", "4", "--", "5", "6"],
            [[type_(i) for i in range(5)], [type_(i) for i in range(5, 7)]],
            {},
        )

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
