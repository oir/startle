from dataclasses import dataclass
from typing import Literal

from pytest import mark

from ._utils import check_args


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
    pass


@mark.parametrize("sides", [4, 6, None])
@mark.parametrize("kind", ["single", "pair", None])
@mark.parametrize("count", [1, 2, None])
def test_recursive_w_defaults(
    sides: int | None, kind: Literal["single", "pair"] | None, count: int | None
) -> None:
    cli_args = []
    config_kwargs = {}
    if sides is not None:
        cli_args += ["--sides", str(sides)]
        config_kwargs["sides"] = sides
    if kind is not None:
        cli_args += ["--kind", kind]
        config_kwargs["kind"] = kind
    if count is not None:
        cli_args += ["--count", str(count)]

    expected_cfg = Config(**config_kwargs)
    expected_count = count if count is not None else 1
    check_args(throw_dice, cli_args, [expected_cfg, expected_count], {}, recurse=True)
