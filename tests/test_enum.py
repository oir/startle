import sys
from enum import Enum, IntEnum
from typing import Callable

from pytest import mark, raises

from startle.error import ParserOptionError, ParserValueError

from ._utils import Opt, Opts, check_args


def check(draw: Callable, shape: type[Enum], opt: Opt):
    check_args(draw, opt("shape", ["square"]), [shape.SQUARE], {})  # type: ignore
    check_args(draw, opt("shape", ["circle"]), [shape.CIRCLE], {})  # type: ignore
    check_args(draw, opt("shape", ["triangle"]), [shape.TRIANGLE], {})  # type: ignore

    with raises(ParserValueError, match="Cannot parse enum Shape from `rectangle`!"):
        check_args(draw, opt("shape", ["rectangle"]), [], {})


def check_with_default(draw: Callable, shape: type[Enum], opt: Opt):
    check_args(draw, [], [shape.CIRCLE], {})  # type: ignore
    check(draw, shape, opt)


@mark.parametrize("opt", Opts())
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


@mark.parametrize("opt", Opts())
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
@mark.parametrize("opt", Opts())
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


@mark.parametrize("opt", Opts())
def test_intenum(opt: Opt):
    class Number(IntEnum):
        ONE_LIKE = 1
        TWO_LIKE = 2
        FOUR_LIKE = 4

    def count(number: Number):
        print(f"Counting {number}.")

    check_args(count, opt("number", ["one-like"]), [Number.ONE_LIKE], {})
    check_args(count, opt("number", ["two-like"]), [Number.TWO_LIKE], {})
    check_args(count, opt("number", ["four-like"]), [Number.FOUR_LIKE], {})
    with raises(ParserValueError, match="Cannot parse enum Number from `three-like`!"):
        check_args(count, opt("number", ["three-like"]), [], {})
    with raises(ParserValueError, match="Cannot parse enum Number from `1`!"):
        check_args(count, opt("number", ["1"]), [], {})


@mark.parametrize("opt", Opts())
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


@mark.parametrize("opt", Opts())
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
