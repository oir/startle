import re
from typing import Callable, Literal

from _utils import check_args
from pytest import mark, raises

from startle.error import ParserValueError


def check(draw: Callable, prefix: list[str]):
    check_args(draw, prefix + ["square"], ["square"], {})
    check_args(draw, prefix + ["circle"], ["circle"], {})
    check_args(draw, prefix + ["triangle"], ["triangle"], {})

    with raises(
        ParserValueError,
        match=re.escape(
            "Cannot parse literal ('square', 'circle', 'triangle') from `rectangle`!"
        ),
    ):
        check_args(draw, prefix + ["rectangle"], [], {})


def check_with_default(draw: Callable, prefix: list[str]):
    if not prefix:
        check_args(draw, [], ["circle"], {})
    check_args(draw, prefix + ["square"], ["square"], {})
    check_args(draw, prefix + ["circle"], ["circle"], {})
    check_args(draw, prefix + ["triangle"], ["triangle"], {})

    with raises(
        ParserValueError,
        match=re.escape(
            "Cannot parse literal ('square', 'circle', 'triangle') from `rectangle`!"
        ),
    ):
        check_args(draw, prefix + ["rectangle"], [], {})


@mark.parametrize("prefix", [[], ["--shape"], ["-s"]])
def test_literal(prefix: list[str]):
    def draw(shape: Literal["square", "circle", "triangle"]):
        print(f"Drawing a {shape}.")

    check(draw, prefix)

    def draw_with_default(shape: Literal["square", "circle", "triangle"] = "circle"):
        print(f"Drawing a {shape}.")

    check_with_default(draw_with_default, prefix)
