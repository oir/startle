"""
A program to throw dice.

Example invocations:
    python examples/dice2.py
    python examples/dice2.py --sides 20 --count 2 --kind pair
"""

import random
from dataclasses import dataclass
from typing import Literal

from startle import start


@dataclass
class Config:
    """
    Configuration for the dice program.

    Attributes:
        sides: The number of sides on the dice.
        kind: Whether to throw a single die or a pair of dice.
    """

    sides: int = 6
    kind: Literal["single", "pair"] = "single"


def throw_dice(cfg: Config, count: int = 1) -> None:
    """
    Throw dice according to the configuration.

    Args:
        cfg: The configuration for the dice.
        count: The number of dice to throw.
    """
    if cfg.kind == "single":
        for _ in range(count):
            print(random.randint(1, cfg.sides))
    else:
        for _ in range(count):
            print(random.randint(1, cfg.sides), random.randint(1, cfg.sides))


if __name__ == "__main__":
    start(throw_dice, recurse=True)
