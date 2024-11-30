import sys
from enum import Enum

from pytest import mark

from ._utils import NS, OS, TS, VS, check_help

expected_w_names = f"""\

Draw a shape.

[{TS}]Usage:[/]
  draw.py [{NS} {OS}]--shape[/] [{VS}]square-opt[/][{VS} dim]|[/][{VS}]circle-opt[/][{VS} dim]|[/][{VS}]triangle-opt[/]

[{TS}]where[/]
  [dim](pos. or opt.)[/]  [{NS} {OS}]-s[/][{OS} dim]|[/][{NS} {OS}]--shape[/] [{VS}]square-opt[/][{VS} dim]|[/][{VS}]circle-opt[/][{VS} dim]|[/][{VS}]triangle-opt[/]  [i]The shape to draw.[/] [yellow](required)[/]   
  [dim](option)[/]        [{NS} {OS} dim]-?[/][{OS} dim]|[/][{NS} {OS} dim]--help[/]                                      [i dim]Show this help message and exit.[/]
"""


expected_w_values = f"""\

Draw a shape.

[{TS}]Usage:[/]
  draw.py [{NS} {OS}]--shape[/] [{VS}]square-like[/][{VS} dim]|[/][{VS}]circle-like[/][{VS} dim]|[/][{VS}]triangle-like[/]

[{TS}]where[/]
  [dim](pos. or opt.)[/]  [{NS} {OS}]-s[/][{OS} dim]|[/][{NS} {OS}]--shape[/] [{VS}]square-like[/][{VS} dim]|[/][{VS}]circle-like[/][{VS} dim]|[/][{VS}]triangle-like[/]  [i]The shape to draw.[/] [yellow](required)[/]   
  [dim](option)[/]        [{NS} {OS} dim]-?[/][{OS} dim]|[/][{NS} {OS} dim]--help[/]                                         [i dim]Show this help message and exit.[/]
"""


def test_enum():
    class Shape(Enum):
        SQUARE_OPT = "square-like"
        CIRCLE_OPT = "circle-like"
        TRIANGLE_OPT = "triangle-like"

    def draw(shape: Shape):
        """
        Draw a shape.

        Args:
            shape: The shape to draw.
        """
        print(f"Drawing a {shape.value}.")

    check_help(draw, "draw.py", expected_w_names)


def test_str_enum_multi_inheritance():
    class Shape(str, Enum):
        SQUARE_OPT = "square-like"
        CIRCLE_OPT = "circle-like"
        TRIANGLE_OPT = "triangle-like"

    def draw(shape: Shape):
        """
        Draw a shape.

        Args:
            shape: The shape to draw.
        """
        print(f"Drawing a {shape.value}.")

    check_help(draw, "draw.py", expected_w_values)


@mark.skipif(
    sys.version_info < (3, 11), reason="Requires Python 3.11 or higher for StrEnum"
)
def test_strenum():
    from enum import StrEnum

    class Shape(StrEnum):
        SQUARE_OPT = "square-like"
        CIRCLE_OPT = "circle-like"
        TRIANGLE_OPT = "triangle-like"

    def draw(shape: Shape):
        """
        Draw a shape.

        Args:
            shape: The shape to draw.
        """
        print(f"Drawing a {shape.value}.")

    check_help(draw, "draw.py", expected_w_values)


def test_intenum():
    from enum import IntEnum

    class Shape(IntEnum):
        SQUARE_OPT = 0
        CIRCLE_OPT = 1
        TRIANGLE_OPT = 2

    def draw(shape: Shape):
        """
        Draw a shape.

        Args:
            shape: The shape to draw.
        """
        print(f"Drawing a {shape.value}.")

    check_help(draw, "draw.py", expected_w_names)
