import re
from typing import Callable, Tuple

from pytest import mark, raises

from startle.error import ParserConfigError, ParserOptionError, ParserValueError

from ._utils import check_args


def add_int(*, numbers: tuple[int, ...]) -> None:
    print(sum(numbers))


def add_float(*, numbers: tuple[float, ...]) -> None:
    print(sum(numbers))


def add_str(*, numbers: tuple[str, ...]) -> None:
    print(" ".join(numbers))


def add_int2(*, numbers: Tuple[int, ...]) -> None:
    print(sum(numbers))


def add_float2(*, numbers: Tuple[float, ...]) -> None:
    print(sum(numbers))


def add_str2(*, numbers: tuple[str, ...]) -> None:
    print(" ".join(numbers))


def add_str3(*, numbers: tuple) -> None:
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
def test_keyword_tuple(add: Callable, scalar: type, opt: str) -> None:
    cli = [opt] + [str(i) for i in range(5)]
    check_args(add, cli, [], {"numbers": tuple([scalar(i) for i in range(5)])})
    cli = [f"{opt}={i}" for i in range(5)]
    check_args(add, cli, [], {"numbers": tuple([scalar(i) for i in range(5)])})

    check_args(
        add,
        ["--numbers", "0", "1", "-n", "2"],
        [],
        {"numbers": tuple([scalar(i) for i in range(3)])},
    )

    with raises(ParserOptionError, match="Required option `numbers` is not provided!"):
        check_args(add, [], [], {})

    if scalar in [int, float]:
        with raises(
            ParserValueError,
            match=f"Cannot parse {'integer' if scalar is int else 'float'} from `x`!",
        ):
            check_args(add, [opt, "0", "1", "x"], [], {})


def addwh1(*, widths: tuple[int, ...], heights: tuple[float, ...] = []) -> None:
    print(sum(widths))
    print(sum(heights))


def addwh2(*, widths: tuple[float, ...], heights: tuple[str, ...] = []) -> None:
    print(sum(widths))
    print(sum(heights))


def addwh3(*, widths: tuple[str, ...], heights: tuple[int, ...] = []) -> None:
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
            "widths": tuple([wscalar(i) for i in range(5)]),
            "heights": tuple([hscalar(i) for i in range(5, 10)]),
        },
    )

    with raises(ParserOptionError, match="Required option `widths` is not provided!"):
        check_args(add, [], [], {})
    with raises(ParserOptionError, match="Required option `widths` is not provided!"):
        check_args(add, [hopt, "0", "1"], [], {})

    cli = [wopt, "0", "1", "2", "3", "4"]
    check_args(
        add, cli, [], {"widths": tuple([wscalar(i) for i in range(5)]), "heights": []}
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


def test_unexpected_tuple_signature():
    def add1(*, numbers: tuple[int]) -> None:
        print(sum(numbers))

    def add2(*, numbers: tuple[int, float]) -> None:
        print(sum(numbers))

    with raises(
        ParserConfigError,
        match=re.escape(
            "Unsupported type `tuple[int]` for parameter `numbers` in `add1()`!"
        ),
    ):
        check_args(add1, [], [], {})

    with raises(
        ParserConfigError,
        match=re.escape(
            "Unsupported type `tuple[int, float]` for parameter `numbers` in `add2()`!"
        ),
    ):
        check_args(add2, [], [], {})
