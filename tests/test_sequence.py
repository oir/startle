import re
from typing import Any, Iterable, List, MutableSequence, Sequence, Tuple

from pytest import mark, raises
from startle.error import ParserConfigError, ParserOptionError, ParserValueError

from ._utils import check_args, copy_function

TUPLE_TYPES = [tuple, Tuple, Iterable, Sequence]


def hint(container: Any, scalar: type | None) -> Any:
    if scalar is None:
        return container
    if container in [tuple, Tuple]:
        return container[scalar, ...]  # type: ignore
    return container[scalar]


def add(*, numbers: list[int]) -> None:
    print(sum(numbers))


@mark.parametrize(
    "container", [list, List, Sequence, MutableSequence, Iterable, tuple, Tuple]
)
@mark.parametrize("scalar", [int, float, str])
@mark.parametrize("opt", ["-n", "--numbers"])
def test_keyword_list(container: Any, scalar: type, opt: str) -> None:
    add_ = copy_function(add, annotations={"numbers": hint(container, scalar)})

    maybe_tuple = tuple if container in TUPLE_TYPES else list

    cli = [opt] + [str(i) for i in range(5)]
    check_args(add_, cli, [], {"numbers": maybe_tuple([scalar(i) for i in range(5)])})

    cli = [f"{opt}={i}" for i in range(5)]
    check_args(add_, cli, [], {"numbers": maybe_tuple([scalar(i) for i in range(5)])})

    check_args(
        add_,
        ["--numbers", "0", "1", "-n", "2"],
        [],
        {"numbers": maybe_tuple([scalar(i) for i in range(3)])},
    )

    with raises(ParserOptionError, match="Required option `numbers` is not provided!"):
        check_args(add_, [], [], {})

    if scalar in [int, float]:
        with raises(
            ParserValueError,
            match=f"Cannot parse {'integer' if scalar is int else 'float'} from `x`!",
        ):
            check_args(add_, [opt, "0", "1", "x"], [], {})


def addwh(*, widths: list[str], heights: list[int] = []) -> None:
    pass


@mark.parametrize(
    "wcontainer", [list, List, Sequence, MutableSequence, Iterable, tuple, Tuple]
)
@mark.parametrize(
    "hcontainer", [list, List, Sequence, MutableSequence, Iterable, tuple, Tuple]
)
@mark.parametrize("wscalar", [int, float, str])
@mark.parametrize("hscalar", [int, float, str])
@mark.parametrize("short", [False, True])
def test_keyword_nargs_long(
    wcontainer: Any, hcontainer: Any, wscalar: type, hscalar: type, short: bool
) -> None:
    add_ = copy_function(
        addwh,
        annotations={
            "widths": hint(wcontainer, wscalar),
            "heights": hint(hcontainer, hscalar),
        },
        kwdefaults={"heights": () if hcontainer in TUPLE_TYPES else []},
    )
    maybe_wtuple = tuple if wcontainer in TUPLE_TYPES else list
    maybe_htuple = tuple if hcontainer in TUPLE_TYPES else list

    wopt = "-w" if short else "--widths"
    hopt = "--heights"
    cli = [wopt, "0", "1", "2", "3", "4", hopt, "5", "6", "7", "8", "9"]
    check_args(
        add_,
        cli,
        [],
        {
            "widths": maybe_wtuple([wscalar(i) for i in range(5)]),
            "heights": maybe_htuple([hscalar(i) for i in range(5, 10)]),
        },
    )

    with raises(ParserOptionError, match="Required option `widths` is not provided!"):
        check_args(add_, [], [], {})
    with raises(ParserOptionError, match="Required option `widths` is not provided!"):
        check_args(add_, [hopt, "0", "1"], [], {})

    cli = [wopt, "0", "1", "2", "3", "4"]
    check_args(
        add_,
        cli,
        [],
        {
            "widths": maybe_wtuple([wscalar(i) for i in range(5)]),
            "heights": maybe_htuple([]),
        },
    )

    with raises(
        ParserOptionError, match=f"Option `{hopt.lstrip('-')}` is missing argument!"
    ):
        check_args(add_, cli + [hopt], [], {})

    if wscalar in [int, float]:
        with raises(
            ParserValueError,
            match=f"Cannot parse {'integer' if wscalar is int else 'float'} from `x`!",
        ):
            check_args(add_, [wopt, "0", "1", "x"], [], {})
    if hscalar in [int, float]:
        with raises(
            ParserValueError,
            match=f"Cannot parse {'integer' if hscalar is int else 'float'} from `x`!",
        ):
            check_args(add_, [wopt, "0", "1", hopt, "0", "1", "x"], [], {})


def add_pos(numbers: list[int], /) -> None:
    pass


@mark.parametrize(
    "container", [list, List, Sequence, MutableSequence, Iterable, tuple, Tuple]
)
@mark.parametrize("scalar", [int, float, str, None])
def test_positional_nargs(container: Any, scalar: type | None) -> None:
    add_ = copy_function(add_pos, annotations={"numbers": hint(container, scalar)})
    maybe_tuple = tuple if container in TUPLE_TYPES else list
    if scalar is None:
        scalar = str

    cli = ["0", "1", "2", "3", "4"]
    check_args(add_, cli, [maybe_tuple([scalar(i) for i in range(5)])], {})

    with raises(ParserOptionError, match="Unexpected option `numbers`!"):
        check_args(add_, ["--numbers", "0", "1", "2", "3", "4"], [], {})
    with raises(
        ParserOptionError,
        match="Required positional argument <numbers> is not provided!",
    ):
        check_args(add_, [], [], {})

    if scalar in [int, float]:
        with raises(
            ParserValueError,
            match=f"Cannot parse {'integer' if scalar is int else 'float'} from `x`!",
        ):
            check_args(add_, ["0", "1", "x"], [], {})


def posd_add(numbers: list[str] = ["3", "5"], /) -> None:
    print(sum(int(n) for n in numbers))


@mark.parametrize(
    "container", [list, List, Sequence, MutableSequence, Iterable, tuple, Tuple]
)
@mark.parametrize("scalar", [int, float, str])
def test_positional_nargs_with_defaults(container: Any, scalar: type) -> None:
    defaults = (
        ([scalar(3), scalar(5)],)
        if container not in TUPLE_TYPES
        else ((scalar(3), scalar(5)),)
    )
    add_ = copy_function(
        posd_add,
        annotations={"numbers": hint(container, scalar)},
        defaults=defaults,
    )
    maybe_tuple = tuple if container in TUPLE_TYPES else list
    cli = ["0", "1", "2", "3", "4"]
    check_args(add_, cli, [maybe_tuple([scalar(i) for i in range(5)])], {})
    check_args(add_, [], [maybe_tuple([scalar(3), scalar(5)])], {})


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

    for rectangle, type_ in [  # type: ignore
        (rectangle_int, int),
        (rectangle_float, float),
        (rectangle_str, str),
    ]:
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
