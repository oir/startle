import sys
from enum import Enum
from typing import Callable

from _utils import check_args
from pytest import mark, raises

from startle.error import ParserValueError


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
