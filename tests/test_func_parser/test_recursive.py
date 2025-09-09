import re
from dataclasses import dataclass, field
from typing import Callable, Literal

from pytest import mark, raises

from startle.error import ParserConfigError, ParserOptionError

from ..test_help._utils import (
    NS,
    OS,
    TS,
    VS,
    check_help_from_func,
)
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


@mark.parametrize("sides_opt", ["--sides", "-s"])
@mark.parametrize("kind_opt", ["--kind", "-k"])
@mark.parametrize("count_opt", ["--count", "-c"])
@mark.parametrize("sides", [4, 6, None])
@mark.parametrize("kind", ["single", "pair", None])
@mark.parametrize("count", [1, 2, None])
def test_recursive_w_defaults(
    sides_opt: str,
    kind_opt: str,
    count_opt: str,
    sides: int | None,
    kind: Literal["single", "pair"] | None,
    count: int | None,
) -> None:
    cli_args = []
    config_kwargs = {}
    if sides is not None:
        cli_args += [sides_opt, str(sides)]
        config_kwargs["sides"] = sides
    if kind is not None:
        cli_args += [kind_opt, kind]
        config_kwargs["kind"] = kind
    if count is not None:
        cli_args += [count_opt, str(count)]

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


@mark.parametrize("sides_opt", ["--sides", "-s"])
@mark.parametrize("kind_opt", ["--kind", "-k"])
@mark.parametrize("count_opt", ["--count", "-c"])
@mark.parametrize("sides", [4, 6, None])
@mark.parametrize("kind", ["single", "pair", None])
@mark.parametrize("count", [1, 2, None])
def test_recursive_w_required(
    sides_opt: str,
    kind_opt: str,
    count_opt: str,
    sides: int | None,
    kind: Literal["single", "pair"] | None,
    count: int | None,
) -> None:
    cli_args = []
    config_kwargs = {}
    if sides is not None:
        cli_args += [sides_opt, str(sides)]
        config_kwargs["sides"] = sides
    if kind is not None:
        cli_args += [kind_opt, kind]
        config_kwargs["kind"] = kind
    if count is not None:
        cli_args += [count_opt, str(count)]

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


def throw_dice4(count: int, cfg: DieConfig2 | None = None) -> None:
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
    check_args(
        throw_dice4,
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
    check_args(
        throw_dice4,
        ["--count", "2"],
        [2, None],
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


@dataclass
class NestedConfigWithVarArgs:
    config: ConfigWithVarArgs


def test_recursive_unsupported() -> None:
    def f1(cfg: ConfigWithVarArgs) -> None:
        pass

    def f2(cfg: ConfigWithVarKwargs) -> None:
        pass

    def f3(cfg: NestedConfigWithVarArgs) -> None:
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
    with raises(
        ParserConfigError,
        match="Cannot have variadic parameter `values` in child Args of `ConfigWithVarArgs`!",
    ):
        check_args(f3, [], [], {}, recurse=True)

    def f4(cfgs: list[DieConfig]) -> None:
        pass

    def f5(*cfgs: DieConfig) -> None:
        pass

    def f6(**cfgs: DieConfig) -> None:
        pass

    with raises(
        ParserConfigError,
        match=re.escape("Cannot recurse into n-ary parameter `cfgs` in `f4()`!"),
    ):
        check_args(f4, [], [], {}, recurse=True)
    with raises(
        ParserConfigError,
        match=re.escape("Cannot recurse into variadic parameter `cfgs` in `f5()`!"),
    ):
        check_args(f5, [], [], {}, recurse=True)
    with raises(
        ParserConfigError,
        match=re.escape("Cannot recurse into variadic parameter `cfgs` in `f6()`!"),
    ):
        check_args(f6, [], [], {}, recurse=True)

    def f7(cfg: DieConfig, sides: int) -> None:
        pass

    def f8(cfg: DieConfig, cfg2: DieConfig) -> None:
        pass

    with raises(
        ParserConfigError,
        match=re.escape(
            "Option name `sides` is used multiple times in `f7()`!"
            " Recursive parsing requires unique option names among all levels."
        ),
    ):
        check_args(f7, [], [], {}, recurse=True)

    with raises(
        ParserConfigError,
        match=re.escape(
            "Option name `sides` is used multiple times in `f8()`!"
            " Recursive parsing requires unique option names among all levels."
        ),
    ):
        check_args(f8, [], [], {}, recurse=True)


@dataclass
class FusionConfig:
    """
    Fusion config.

    Attributes:
        left_path: Path to the first monster.
        right_path: Path to the second monster.
        output_path [p]: Path to store the fused monster.
        components: Components to fuse.
        alpha: Weighting factor for the first monster.
    """

    left_path: str
    right_path: str
    output_path: str
    components: list[str] = field(default_factory=lambda: ["fang", "claw"])
    alpha: float = 0.5


@dataclass
class InputPaths:
    """
    Input paths for fusion.

    Attributes:
        left_path: Path to the first monster.
        right_path: Path to the second monster.
    """

    left_path: str
    right_path: str


@dataclass
class IOPaths:
    """
    Input and output paths for fusion.

    Attributes:
        input_paths: Input paths for the fusion.
        output_path [p]: Path to store the fused monster.
    """

    input_paths: InputPaths
    output_path: str


@dataclass
class FusionConfig2:
    """
    Fusion config with separate input and output paths.

    Attributes:
        io_paths: Input and output paths for the fusion.
        components: Components to fuse.
        alpha: Weighting factor for the first monster.
    """

    io_paths: IOPaths
    components: list[str] = field(default_factory=lambda: ["fang", "claw"])
    alpha: float = 0.5


def fuse1(cfg: FusionConfig) -> None:
    """
    Fuse two monsters with polymerization.

    Args:
        cfg: The fusion configuration.
    """
    pass


def fuse2(cfg: FusionConfig2) -> None:
    """
    Fuse two monsters with polymerization.

    Args:
        cfg: The fusion configuration.
    """
    pass


@mark.parametrize("fuse", [fuse1, fuse2])
def test_recursive_dataclass_help(fuse: Callable) -> None:
    if fuse is fuse1:
        expected = FusionConfig(
            left_path="monster1.dat",
            right_path="monster2.dat",
            output_path="fused_monster.dat",
            components=["wing", "tail"],
            alpha=0.7,
        )
    else:
        expected = FusionConfig2(
            io_paths=IOPaths(
                input_paths=InputPaths(
                    left_path="monster1.dat", right_path="monster2.dat"
                ),
                output_path="fused_monster.dat",
            ),
            components=["wing", "tail"],
            alpha=0.7,
        )
    check_args(
        fuse,
        [
            "--left-path",
            "monster1.dat",
            "--right-path",
            "monster2.dat",
            "--output-path",
            "fused_monster.dat",
            "--components",
            "wing",
            "tail",
            "--alpha",
            "0.7",
        ],
        [expected],
        {},
        recurse=True,
    )

    expected = f"""\

Fuse two monsters with polymerization.

[{TS}]Usage:[/]
  fuse.py [{NS} {OS}]--left-path[/] [{VS}]<text>[/] [{NS} {OS}]--right-path[/] [{VS}]<text>[/] [{NS} {OS}]--output-path[/] [{VS}]<text>[/] [[{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]] [[{NS} {OS}]--alpha[/] [{VS}]<float>[/]]

[{TS}]where[/]
  [dim](option)[/]  [{NS} {OS}]-l[/][{OS} dim]|[/][{NS} {OS}]--left-path[/] [{VS}]<text>[/]                [i]Path to the first monster.[/] [yellow](required)[/]                 
  [dim](option)[/]  [{NS} {OS}]-r[/][{OS} dim]|[/][{NS} {OS}]--right-path[/] [{VS}]<text>[/]               [i]Path to the second monster.[/] [yellow](required)[/]                
  [dim](option)[/]  [{NS} {OS}]-p[/][{OS} dim]|[/][{NS} {OS}]--output-path[/] [{VS}]<text>[/]              [i]Path to store the fused monster.[/] [yellow](required)[/]           
  [dim](option)[/]  [{NS} {OS}]-c[/][{OS} dim]|[/][{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]  [i]Components to fuse.[/] [green](default: [/][green]['fang', 'claw'][/][green])[/]       
  [dim](option)[/]  [{NS} {OS}]-a[/][{OS} dim]|[/][{NS} {OS}]--alpha[/] [{VS}]<float>[/]                   [i]Weighting factor for the first monster.[/] [green](default: [/][green]0.5[/][green])[/]
  [dim](option)[/]  [{NS} {OS} dim]-?[/][{OS} dim]|[/][{NS} {OS} dim]--help[/]                            [i dim]Show this help message and exit.[/]                      
"""
    check_help_from_func(fuse, "fuse.py", expected, recurse=True)


@dataclass
class IOPaths2:
    """
    Input and output paths for fusion.

    Attributes:
        input_paths: Input paths for the fusion.
        output_path [l]: Path to store the fused monster.
    """

    input_paths: InputPaths
    output_path: str


@dataclass
class FusionConfig3:
    """
    Fusion config with separate input and output paths.

    Attributes:
        io_paths: Input and output paths for the fusion.
        components: Components to fuse.
        alpha: Weighting factor for the first monster.
    """

    io_paths: IOPaths2
    components: list[str] = field(default_factory=lambda: ["fang", "claw"])
    alpha: float = 0.5


def fuse3(cfg: FusionConfig3) -> None:
    """
    Fuse two monsters with polymerization.

    Args:
        cfg: The fusion configuration.
    """
    pass


def test_recursive_dataclass_help_2() -> None:
    expected = f"""\

Fuse two monsters with polymerization.

[{TS}]Usage:[/]
  fuse.py [{NS} {OS}]--left-path[/] [{VS}]<text>[/] [{NS} {OS}]--right-path[/] [{VS}]<text>[/] [{NS} {OS}]--output-path[/] [{VS}]<text>[/] [[{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]] [[{NS} {OS}]--alpha[/] [{VS}]<float>[/]]

[{TS}]where[/]
  [dim](option)[/]  [{NS} {OS}]--left-path[/] [{VS}]<text>[/]                   [i]Path to the first monster.[/] [yellow](required)[/]                 
  [dim](option)[/]  [{NS} {OS}]-r[/][{OS} dim]|[/][{NS} {OS}]--right-path[/] [{VS}]<text>[/]               [i]Path to the second monster.[/] [yellow](required)[/]                
  [dim](option)[/]  [{NS} {OS}]-l[/][{OS} dim]|[/][{NS} {OS}]--output-path[/] [{VS}]<text>[/]              [i]Path to store the fused monster.[/] [yellow](required)[/]           
  [dim](option)[/]  [{NS} {OS}]-c[/][{OS} dim]|[/][{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]  [i]Components to fuse.[/] [green](default: [/][green]['fang', 'claw'][/][green])[/]       
  [dim](option)[/]  [{NS} {OS}]-a[/][{OS} dim]|[/][{NS} {OS}]--alpha[/] [{VS}]<float>[/]                   [i]Weighting factor for the first monster.[/] [green](default: [/][green]0.5[/][green])[/]
  [dim](option)[/]  [{NS} {OS} dim]-?[/][{OS} dim]|[/][{NS} {OS} dim]--help[/]                            [i dim]Show this help message and exit.[/]                      
"""
    check_help_from_func(fuse3, "fuse.py", expected, recurse=True)
