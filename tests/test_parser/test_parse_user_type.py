import re
from dataclasses import dataclass

from pytest import raises

from startle import register_type
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


def test_unsupported_type():
    with raises(
        ParserConfigError,
        match=re.escape("Unsupported type `Rational` for parameter `a` in `mul()`!"),
    ):
        check_args(mul, ["1/2", "3/4"], [], {})

    register_type(
        Rational,
        parser=lambda value: Rational(*map(int, value.split("/"))),
        metavar="<int>/<int>",
    )

    check_args(mul, ["1/2", "3/4"], [Rational(1, 2), Rational(3, 4)], {})
