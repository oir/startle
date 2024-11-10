import sys
from enum import Enum, IntEnum
from typing import Callable

from _utils import check_args
from pytest import mark, raises

from startle.error import ParserOptionError, ParserValueError


def positional(name: str, value: list[str]) -> list[str]:
    return value


def short(name: str, value: list[str]) -> list[str]:
    return [f"-{name[0]}"] + value


def long(name: str, value: list[str]) -> list[str]:
    return [f"--{name}"] + value


def short_eq(name: str, value: list[str]) -> list[str]:
    return [f"-{name[0]}={item}" for item in value]


def long_eq(name: str, value: list[str]) -> list[str]:
    return [f"--{name}={item}" for item in value]


Opt = Callable[[str, list[str]], list[str]]


def check(draw: Callable, shape: type[Enum], opt: Opt):
    check_args(draw, opt("shape", ["square"]), [shape.SQUARE], {})
    check_args(draw, opt("shape", ["circle"]), [shape.CIRCLE], {})
    check_args(draw, opt("shape", ["triangle"]), [shape.TRIANGLE], {})

    with raises(ParserValueError, match="Cannot parse enum Shape from `rectangle`!"):
        check_args(draw, opt("shape", ["rectangle"]), [], {})


def check_with_default(draw: Callable, shape: type[Enum], opt: Opt):
    check_args(draw, [], [shape.CIRCLE], {})
    check(draw, shape, opt)


@mark.parametrize("opt", [positional, short, long, short_eq, long_eq])
def test_enum(opt: Opt):
    class Shape(Enum):
        SQUARE = "square"
        CIRCLE = "circle"
        TRIANGLE = "triangle"

    def draw(shape: Shape):
        print(f"Drawing a {shape.value}.")

    check(draw, Shape, opt)

    def draw_with_default(shape: Shape = Shape.CIRCLE):
        print(f"Drawing a {shape.value}.")

    check_with_default(draw_with_default, Shape, opt)


@mark.parametrize("opt", [positional, short, long, short_eq, long_eq])
def test_str_enum_multi_inheritance(opt: Opt):
    class Shape(str, Enum):
        SQUARE = "square"
        CIRCLE = "circle"
        TRIANGLE = "triangle"

    def draw(shape: Shape):
        print(f"Drawing a {shape.value}.")

    check(draw, Shape, opt)

    def draw_with_default(shape: Shape = Shape.CIRCLE):
        print(f"Drawing a {shape.value}.")

    check_with_default(draw_with_default, Shape, opt)


@mark.skipif(
    sys.version_info < (3, 11), reason="Requires Python 3.11 or higher for StrEnum"
)
@mark.parametrize("opt", [positional, short, long, short_eq, long_eq])
def test_strenum(opt: Opt):
    from enum import StrEnum

    class Shape(StrEnum):
        SQUARE = "square"
        CIRCLE = "circle"
        TRIANGLE = "triangle"

    def draw(shape: Shape):
        print(f"Drawing a {shape.value}.")

    check(draw, Shape, opt)

    def draw_with_default(shape: Shape = Shape.CIRCLE):
        print(f"Drawing a {shape.value}.")

    check_with_default(draw_with_default, Shape, opt)


@mark.parametrize("opt", [positional, short, long, short_eq, long_eq])
def test_intenum(opt: Opt):
    class Number(IntEnum):
        ONE = 1
        TWO = 2
        FOUR = 4

    def count(number: Number):
        print(f"Counting {number}.")

    check_args(count, opt("number", ["1"]), [Number.ONE], {})
    check_args(count, opt("number", ["2"]), [Number.TWO], {})
    check_args(count, opt("number", ["4"]), [Number.FOUR], {})
    with raises(ParserValueError, match="Cannot parse enum Number from `3`!"):
        check_args(count, opt("number", ["3"]), [], {})


@mark.parametrize("opt", [positional, short, long, short_eq, long_eq])
def test_optional_enum(opt: Opt):
    class Shape(Enum):
        SQUARE = "square"
        CIRCLE = "circle"
        TRIANGLE = "triangle"

    def draw(shape: Shape | None = None):
        if shape is None:
            print("No shape to draw.")
        else:
            print(f"Drawing a {shape.value}.")

    check(draw, Shape, opt)
    check_args(draw, [], [None], {})


@mark.parametrize("opt", [positional, short, long, short_eq, long_eq])
def test_enum_list(opt: Opt):
    class Shape(Enum):
        SQUARE = "square"
        CIRCLE = "circle"
        TRIANGLE = "triangle"

    def draw(shapes: list[Shape]):
        for shape in shapes:
            print(f"Drawing a {shape.value}.")

    check_args(draw, opt("shapes", ["square"]), [[Shape.SQUARE]], {})
    check_args(
        draw,
        opt("shapes", ["circle", "square"]),
        [[Shape.CIRCLE, Shape.SQUARE]],
        {},
    )
    check_args(
        draw,
        opt("shapes", ["triangle", "circle", "square", "circle"]),
        [[Shape.TRIANGLE, Shape.CIRCLE, Shape.SQUARE, Shape.CIRCLE]],
        {},
    )

    with raises(ParserValueError, match="Cannot parse enum Shape from `rectangle`!"):
        check_args(draw, opt("shapes", ["rectangle"]), [], {})
    with raises(ParserValueError, match="Cannot parse enum Shape from `rectangle`!"):
        check_args(draw, opt("shapes", ["triangle", "circle", "rectangle"]), [], {})
    with raises(ParserOptionError, match="Required option `shapes` is not provided!"):
        check_args(draw, [], [], {})
