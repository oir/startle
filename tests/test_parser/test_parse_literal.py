import re
from typing import Callable, Literal

from ._utils import Opt, Opts, check_args
from pytest import mark, raises

from startle.error import ParserValueError


def check(draw: Callable, opt: Opt):
    check_args(draw, opt("shape", ["square"]), ["square"], {})
    check_args(draw, opt("shape", ["circle"]), ["circle"], {})
    check_args(draw, opt("shape", ["triangle"]), ["triangle"], {})

    with raises(
        ParserValueError,
        match=re.escape(
            "Cannot parse literal ('square', 'circle', 'triangle') from `rectangle`!"
        ),
    ):
        check_args(draw, opt("shape", ["rectangle"]), [], {})


def check_with_default(draw: Callable, opt: Opt):
    check_args(draw, [], ["circle"], {})
    check(draw, opt)


@mark.parametrize("opt", Opts())
def test_literal(opt: Opt):
    def draw(shape: Literal["square", "circle", "triangle"]):
        print(f"Drawing a {shape}.")

    check(draw, opt)

    def draw_with_default(shape: Literal["square", "circle", "triangle"] = "circle"):
        print(f"Drawing a {shape}.")

    check_with_default(draw_with_default, opt)
