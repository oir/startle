from dataclasses import dataclass

from startle import register, start


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


register(
    Rational,
    parser=lambda value: Rational(*map(int, value.split("/"))),
    metavar=["<int>/<int>"],
)
start(mul)
