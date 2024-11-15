from typing import Callable, Set

from _utils import check_args
from pytest import mark, raises

from startle.error import ParserOptionError, ParserValueError


def add_int(*, numbers: set[int]) -> None:
    print(sum(numbers))


def add_float(*, numbers: set[float]) -> None:
    print(sum(numbers))


def add_str(*, numbers: set[str]) -> None:
    print(" ".join(numbers))


def add_int2(*, numbers: Set[int]) -> None:
    print(sum(numbers))


def add_float2(*, numbers: Set[float]) -> None:
    print(sum(numbers))


def add_str2(*, numbers: set[str]) -> None:
    print(" ".join(numbers))


def add_str3(*, numbers: set) -> None:
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
        (add_str3, str),
    ],
)
@mark.parametrize("opt", ["-n", "--numbers"])
def test_keyword_set(add: Callable, scalar: type, opt: str) -> None:
    cli = [opt] + [str(i) for i in range(5)]
    check_args(add, cli, [], {"numbers": set([scalar(i) for i in range(5)])})
    cli = [f"{opt}={i}" for i in range(5)]
    check_args(add, cli, [], {"numbers": set([scalar(i) for i in range(5)])})

    check_args(
        add,
        ["--numbers", "0", "1", "-n", "2"],
        [],
        {"numbers": set([scalar(i) for i in range(3)])},
    )

    with raises(ParserOptionError, match="Required option `numbers` is not provided!"):
        check_args(add, [], [], {})

    if scalar in [int, float]:
        with raises(
            ParserValueError,
            match=f"Cannot parse {'integer' if scalar is int else 'float'} from `x`!",
        ):
            check_args(add, [opt, "0", "1", "x"], [], {})


def addwh1(*, widths: set[int], heights: set[float] = []) -> None:
    print(sum(widths))
    print(sum(heights))


def addwh2(*, widths: set[float], heights: set[str] = []) -> None:
    print(sum(widths))
    print(sum(heights))


def addwh3(*, widths: set[str], heights: set[int] = []) -> None:
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
            "widths": set([wscalar(i) for i in range(5)]),
            "heights": set([hscalar(i) for i in range(5, 10)]),
        },
    )

    with raises(ParserOptionError, match="Required option `widths` is not provided!"):
        check_args(add, [], [], {})
    with raises(ParserOptionError, match="Required option `widths` is not provided!"):
        check_args(add, [hopt, "0", "1"], [], {})

    cli = [wopt, "0", "1", "2", "3", "4"]
    check_args(
        add, cli, [], {"widths": set([wscalar(i) for i in range(5)]), "heights": []}
    )

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
