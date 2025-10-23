"""
A program to throw dice.

Example invocations:
    python examples/dice3.py --sides 20 --count 2 --kind pair
"""

import random
from typing import Literal, NotRequired, TypedDict

from startle import parse


class Config(TypedDict):
    """
    Configuration for the dice program.

    Attributes:
        sides: The number of sides on the dice.
        count: The number of dice to throw.
        kind: Whether to throw a single die or a pair of dice.
    """

    sides: NotRequired[int]
    count: int
    kind: Literal["single", "pair"]


def throw_dice(cfg: Config) -> None:
    """
    Throw the dice according to the configuration.
    """
    if cfg["kind"] == "single":
        for _ in range(cfg["count"]):
            print(random.randint(1, cfg.get("sides", 6)))
    else:
        for _ in range(cfg["count"]):
            print(
                random.randint(1, cfg.get("sides", 6)),
                random.randint(1, cfg.get("sides", 6)),
            )


if __name__ == "__main__":
    cfg = parse(Config, brief="A program to throw dice.")
    throw_dice(cfg)
