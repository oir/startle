"""
Example invocations:
    python examples/color.py Alice
    python examples/color.py --name Bob --color green --style dim

Test 'choices' check by trying to pass an invalid color or style:
    python examples/color.py --name Alice --color yellow
    python examples/color.py --name Alice --style cursive
"""

from enum import Enum
from typing import Literal

from rich.console import Console

from startle import start


class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


def hi(
    name: str,
    color: Color = Color.RED,
    style: Literal["bold", "dim", "italic"] = "bold",
) -> None:
    console = Console()
    console.print(f"[{color.value} {style}]{name}[/]")


start(hi)
