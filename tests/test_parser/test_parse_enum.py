import sys
from enum import Enum, IntEnum
from typing import Callable

from _utils import check_args
from pytest import mark, raises

from startle.error import ParserOptionError, ParserValueError


def check(draw: Callable, shape: type[Enum], prefix: list[str]):
    check_args(draw, prefix + ["square"], [], {"shape": shape.SQUARE})
    check_args(draw, prefix + ["circle"], [], {"shape": shape.CIRCLE})
    check_args(draw, prefix + ["triangle"], [], {"shape": shape.TRIANGLE})

    with raises(ParserValueError, match="Cannot parse enum Shape from `rectangle`!"):
        check_args(draw, prefix + ["rectangle"], [], {})


def check_with_default(draw: Callable, shape: type[Enum], prefix: list[str]):
    if not prefix:
        check_args(draw, [], [], {"shape": shape.CIRCLE})
    check_args(draw, prefix + ["square"], [], {"shape": shape.SQUARE})
    check_args(draw, prefix + ["circle"], [], {"shape": shape.CIRCLE})
    check_args(draw, prefix + ["triangle"], [], {"shape": shape.TRIANGLE})

    with raises(ParserValueError, match="Cannot parse enum Shape from `rectangle`!"):
        check_args(draw, prefix + ["rectangle"], [], {})


@mark.parametrize("prefix", [[], ["--shape"], ["-s"]])
def test_enum(prefix: list[str]):
    class Shape(Enum):
        SQUARE = "square"
        CIRCLE = "circle"
        TRIANGLE = "triangle"

    def draw(shape: Shape):
        print(f"Drawing a {shape.value}.")

    check(draw, Shape, prefix)

    def draw_with_default(shape: Shape = Shape.CIRCLE):
        print(f"Drawing a {shape.value}.")

    check_with_default(draw_with_default, Shape, prefix)


@mark.parametrize("prefix", [[], ["--shape"], ["-s"]])
def test_str_enum_multi_inheritance(prefix: list[str]):
    class Shape(str, Enum):
        SQUARE = "square"
        CIRCLE = "circle"
        TRIANGLE = "triangle"

    def draw(shape: Shape):
        print(f"Drawing a {shape.value}.")

    check(draw, Shape, prefix)

    def draw_with_default(shape: Shape = Shape.CIRCLE):
        print(f"Drawing a {shape.value}.")

    check_with_default(draw_with_default, Shape, prefix)


@mark.skipif(
    sys.version_info < (3, 11), reason="Requires Python 3.11 or higher for StrEnum"
)
@mark.parametrize("prefix", [[], ["--shape"], ["-s"]])
def test_strenum(prefix: list[str]):
    from enum import StrEnum

    class Shape(StrEnum):
        SQUARE = "square"
        CIRCLE = "circle"
        TRIANGLE = "triangle"

    def draw(shape: Shape):
        print(f"Drawing a {shape.value}.")

    check(draw, Shape, prefix)

    def draw_with_default(shape: Shape = Shape.CIRCLE):
        print(f"Drawing a {shape.value}.")

    check_with_default(draw_with_default, Shape, prefix)


@mark.parametrize("prefix", [[], ["--number"], ["-n"]])
def test_intenum(prefix: list[str]):
    class Number(IntEnum):
        ONE = 1
        TWO = 2
        FOUR = 4

    def count(number: Number):
        print(f"Counting {number}.")

    check_args(count, prefix + ["1"], [], {"number": Number.ONE})
    check_args(count, prefix + ["2"], [], {"number": Number.TWO})
    check_args(count, prefix + ["4"], [], {"number": Number.FOUR})
    with raises(ParserValueError, match="Cannot parse enum Number from `3`!"):
        check_args(count, prefix + ["3"], [], {})


@mark.parametrize("prefix", [[], ["--shapes"], ["-s"]])
def test_enum_list(prefix: list[str]):
    class Shape(Enum):
        SQUARE = "square"
        CIRCLE = "circle"
        TRIANGLE = "triangle"

    def draw(shapes: list[Shape]):
        for shape in shapes:
            print(f"Drawing a {shape.value}.")

    check_args(draw, prefix + ["square"], [], {"shapes": [Shape.SQUARE]})
    check_args(
        draw,
        prefix + ["circle", "square"],
        [],
        {"shapes": [Shape.CIRCLE, Shape.SQUARE]},
    )
    check_args(
        draw,
        prefix + ["triangle", "circle", "square", "circle"],
        [],
        {"shapes": [Shape.TRIANGLE, Shape.CIRCLE, Shape.SQUARE, Shape.CIRCLE]},
    )

    with raises(ParserValueError, match="Cannot parse enum Shape from `rectangle`!"):
        check_args(draw, prefix + ["rectangle"], [], {})
    with raises(ParserValueError, match="Cannot parse enum Shape from `rectangle`!"):
        check_args(draw, prefix + ["triangle", "circle", "rectangle"], [], {})
    with raises(ParserOptionError, match="Required option `shapes` is not provided!"):
        check_args(draw, [], [], {})
