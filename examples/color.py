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


class Color(str, Enum):
    RED_LIKE = "red"
    GREEN_LIKE = "green"
    BLUE_LIKE = "blue"


class Verbosity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


def hi(
    name: str,
    color: Color = Color.RED_LIKE,
    style: Literal["bold", "dim", "italic"] = "bold",
    verbosity: Verbosity = Verbosity.LOW,
) -> None:
    console = Console()
    for _ in range(verbosity.value):
        console.print(f"[{color.value} {style}]{name}[/]")


start(hi)
