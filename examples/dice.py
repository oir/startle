"""
A program to throw dice.

Example invocations:
    python examples/dice.py
    python examples/dice.py --sides 20 --count 2 --kind pair
"""

import random
from dataclasses import dataclass
from typing import Literal

from startle import parse


@dataclass
class Config:
    """
    Configuration for the dice program.

    Attributes:
        sides: The number of sides on the dice.
        count: The number of dice to throw.
        kind: Whether to throw a single die or a pair of dice.
    """

    sides: int = 6
    count: int = 1
    kind: Literal["single", "pair"] = "single"


def throw_dice(cfg: Config) -> None:
    """
    Throw the dice according to the configuration.
    """
    if cfg.kind == "single":
        for _ in range(cfg.count):
            print(random.randint(1, cfg.sides))
    else:
        for _ in range(cfg.count):
            print(random.randint(1, cfg.sides), random.randint(1, cfg.sides))


if __name__ == "__main__":
    cfg = parse(Config, brief="A program to throw dice.")
    throw_dice(cfg)
