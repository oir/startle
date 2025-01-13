"""
Example invocations:
    python examples/truecolor.py --text hello --red 255 --green 10 --blue 10
    python examples/truecolor.py hello 255 10 10 bold
"""

from dataclasses import dataclass
from typing import Literal

from rich.console import Console

from startle import parse


@dataclass
class StyledText:
    """
    A styled text with color.

    Attributes:
        text: The text to display.
        red: The red component of the text color.
        green: The green component of the text color.
        blue: The blue component of the text color.
        style: The style of the text.
    """

    text: str
    red: int
    green: int
    blue: int
    style: Literal["default", "bold", "dim", "italic"] = "default"


def display(st: StyledText) -> None:
    console = Console()
    console.print(f"[rgb({st.red},{st.green},{st.blue}) {st.style}]{st.text}[/]")


if __name__ == "__main__":
    cfg = parse(StyledText, brief="Print styled text.")
    display(cfg)
