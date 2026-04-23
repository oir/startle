import re
from dataclasses import dataclass

from pytest import raises
from rich.console import Console
from startle import register
from startle._inspect.make_args import make_args_from_func
from startle._metavar import METAVARS
from startle._value_parser import PARSERS
from startle.error import ParserConfigError

from ._utils import check_args


@dataclass
class Rational:
    num: int
    den: int

    def __repr__(self):
        return f"{self.num}/{self.den}"


def mul(a: Rational, b: Rational) -> Rational:
    """
    Multiply two rational numbers.
    """
    y = Rational(a.num * b.num, a.den * b.den)
    print(f"{a} * {b} = {y}")
    return y


def mul2(ns: list[Rational]) -> Rational:
    """
    Multiply a list of rational numbers.
    """
    y = Rational(1, 1)
    for n in ns:
        y.num *= n.num
        y.den *= n.den
    print(f"{' * '.join(map(str, ns))} = {y}")
    return y


def test_unsupported_type():
    with raises(
        ParserConfigError,
        match=re.escape("Unsupported type `Rational` for parameter `a` in `mul()`!"),
    ):
        check_args(mul, ["1/2", "3/4"], [], {})

    with raises(
        ParserConfigError,
        match=re.escape(
            "Unsupported type `list[Rational]` for parameter `ns` in `mul2()`!"
        ),
    ):
        check_args(mul2, ["1/2", "3/4"], [], {})

    register(
        Rational,
        parser=lambda value: Rational(*map(int, value.split("/"))),
        metavar="<int>/<int>",
    )

    check_args(mul, ["1/2", "3/4"], [Rational(1, 2), Rational(3, 4)], {})
    check_args(mul, ["-a", "1/2", "3/4"], [Rational(1, 2), Rational(3, 4)], {})
    check_args(mul, ["-a", "1/2", "-b", "3/4"], [Rational(1, 2), Rational(3, 4)], {})
    check_args(mul, ["1/2", "-b", "3/4"], [Rational(1, 2), Rational(3, 4)], {})
    check_args(mul, ["-b", "3/4", "1/2"], [Rational(1, 2), Rational(3, 4)], {})
    check_args(mul, ["-b", "3/4", "--", "1/2"], [Rational(1, 2), Rational(3, 4)], {})
    check_args(mul2, ["1/2", "3/4"], [[Rational(1, 2), Rational(3, 4)]], {})
    check_args(mul2, ["--ns", "1/2", "3/4"], [[Rational(1, 2), Rational(3, 4)]], {})

    del PARSERS[Rational]
    del METAVARS[Rational]


def test_unsupported_type_wo_meta():
    with raises(
        ParserConfigError,
        match=re.escape("Unsupported type `Rational` for parameter `a` in `mul()`!"),
    ):
        check_args(mul, ["1/2", "3/4"], [], {})

    with raises(
        ParserConfigError,
        match=re.escape(
            "Unsupported type `list[Rational]` for parameter `ns` in `mul2()`!"
        ),
    ):
        check_args(mul2, ["1/2", "3/4"], [], {})

    register(
        Rational,
        parser=lambda value: Rational(*map(int, value.split("/"))),
    )

    check_args(mul, ["1/2", "3/4"], [Rational(1, 2), Rational(3, 4)], {})
    check_args(mul2, ["1/2", "3/4"], [[Rational(1, 2), Rational(3, 4)]], {})

    assert Rational not in METAVARS
    del PARSERS[Rational]


def test_supported_type_new_meta():
    def mul3(a: float, b: float) -> float:
        """
        Multiply two floats.
        """
        y = a * b
        print(f"{a} * {b} = {y}")
        return y

    check_args(mul3, ["1.0", "2.0"], [1.0, 2.0], {})

    old_meta = METAVARS[float]

    console = Console(width=120, highlight=False, force_terminal=True)
    with console.capture() as cap:
        make_args_from_func(mul3).print_help(console)
    help_before = cap.get()
    assert "<float>" in help_before
    assert "<x.y>" not in help_before

    register(float, metavar="x.y")

    console = Console(width=120, highlight=False, force_terminal=True)
    with console.capture() as cap:
        make_args_from_func(mul3).print_help(console)
    help_after = cap.get()
    assert "<x.y>" in help_after
    assert "<float>" not in help_after

    check_args(mul3, ["1.0", "2.0"], [1.0, 2.0], {})
    assert METAVARS[float] == "x.y"

    # restore old metavar
    METAVARS[float] = old_meta
