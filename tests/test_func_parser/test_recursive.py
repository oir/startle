import re
from dataclasses import dataclass
from typing import Literal

from pytest import mark, raises

from startle.error import ParserConfigError, ParserOptionError

from ._utils import check_args


@dataclass
class DieConfig:
    """
    Configuration for the dice program.

    Attributes:
        sides: The number of sides on the dice.
        kind: Whether to throw a single die or a pair of dice.
    """

    sides: int = 6
    kind: Literal["single", "pair"] = "single"


def throw_dice(cfg: DieConfig, count: int = 1) -> None:
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

    expected_cfg = DieConfig(**config_kwargs)
    expected_count = count if count is not None else 1
    check_args(throw_dice, cli_args, [expected_cfg, expected_count], {}, recurse=True)


@dataclass
class DieConfig2:
    """
    Configuration for the dice program.

    Attributes:
        sides: The number of sides on the dice.
        kind: Whether to throw a single die or a pair of dice.
    """

    sides: int
    kind: Literal["single", "pair"]


def throw_dice2(cfg: DieConfig2, count: int) -> None:
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
def test_recursive_w_required(
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

    if sides is None:
        with raises(
            ParserOptionError, match="Required option `sides` is not provided!"
        ):
            check_args(throw_dice2, cli_args, [], {}, recurse=True)
    elif kind is None:
        with raises(ParserOptionError, match="Required option `kind` is not provided!"):
            check_args(throw_dice2, cli_args, [], {}, recurse=True)
    elif count is None:
        with raises(
            ParserOptionError, match="Required option `count` is not provided!"
        ):
            check_args(throw_dice2, cli_args, [], {}, recurse=True)
    else:
        expected_cfg = DieConfig2(**config_kwargs)
        expected_count = count if count is not None else 1
        check_args(
            throw_dice2, cli_args, [expected_cfg, expected_count], {}, recurse=True
        )


def throw_dice3(
    count: int, cfg: DieConfig2 = DieConfig2(sides=6, kind="single")
) -> None:
    """
    Throw dice according to the configuration.

    Args:
        count: The number of dice to throw.
        cfg: The configuration for the dice.
    """
    pass


def test_recursive_w_inner_required() -> None:
    check_args(
        throw_dice3,
        ["--sides", "4", "--kind", "pair", "--count", "2"],
        [2, DieConfig2(sides=4, kind="pair")],
        {},
        recurse=True,
    )

    # DieConfig2 requires sides and kind, however cfg has a default.
    check_args(
        throw_dice3,
        ["--count", "2"],
        [2, DieConfig2(sides=6, kind="single")],
        {},
        recurse=True,
    )

    # TODO: Decide if this should be handled differently.
    # Because --kind is required for DieConfig2 but not provided,
    # we will fail to parse and use the default for cfg.
    # But because --sides is then not consumed by the child parser,
    # it will surface up to the parent as an unexpected option.
    with raises(ParserOptionError, match="Unexpected option `sides`!"):
        check_args(
            throw_dice3,
            ["--count", "2", "--sides", "4"],
            [2, DieConfig2(sides=6, kind="single")],
            {},
            recurse=True,
        )


class ConfigWithVarArgs:
    def __init__(self, *values: int) -> None:
        self.values = list(values)


class ConfigWithVarKwargs:
    def __init__(self, **settings: int) -> None:
        self.settings = settings


def test_recursive_unsupported() -> None:
    def f1(cfg: ConfigWithVarArgs) -> None:
        pass

    def f2(cfg: ConfigWithVarKwargs) -> None:
        pass

    with raises(
        ParserConfigError,
        match="Cannot have variadic parameter `values` in child Args of `ConfigWithVarArgs`!",
    ):
        check_args(f1, [], [], {}, recurse=True)
    with raises(
        ParserConfigError,
        match="Cannot have variadic parameter `settings` in child Args of `ConfigWithVarKwargs`!",
    ):
        check_args(f2, [], [], {}, recurse=True)

    def f3(cfgs: list[DieConfig]) -> None:
        pass

    def f4(*cfgs: DieConfig) -> None:
        pass

    def f5(**cfgs: DieConfig) -> None:
        pass

    with raises(
        ParserConfigError,
        match=re.escape("Cannot recurse into n-ary parameter `cfgs` in `f3()`!"),
    ):
        check_args(f3, [], [], {}, recurse=True)
    with raises(
        ParserConfigError,
        match=re.escape("Cannot recurse into variadic parameter `cfgs` in `f4()`!"),
    ):
        check_args(f4, [], [], {}, recurse=True)
    with raises(
        ParserConfigError,
        match=re.escape("Cannot recurse into variadic parameter `cfgs` in `f5()`!"),
    ):
        check_args(f5, [], [], {}, recurse=True)

    def f6(cfg: DieConfig, sides: int) -> None:
        pass

    def f7(cfg: DieConfig, cfg2: DieConfig) -> None:
        pass

    with raises(
        ParserConfigError,
        match=re.escape(
            "Option name `sides` is used multiple times in `f6()`!"
            " Recursive parsing requires unique option names among all levels."
        ),
    ):
        check_args(f6, [], [], {}, recurse=True)

    with raises(
        ParserConfigError,
        match=re.escape(
            "Option name `sides` is used multiple times in `DieConfig`!"
            " Recursive parsing requires unique option names among all levels."
        ),
    ):
        check_args(f7, [], [], {}, recurse=True)
