import re
from collections.abc import Callable
from typing import Any, Literal

from pytest import mark, raises
from startle.error import ParserConfigError, ParserOptionError

from .._utils import check_args
from ..test_help._utils import NS, OS, TS, VS, check_help_from_func
from .defs import (
    AppleConfig,
    BananaConfig,
    ConfigWithVarArgs,
    ConfigWithVarKwargs,
    DieConfig,
    DieConfig2,
    DieConfig2TD,
    FusionConfig,
    FusionConfig2,
    FusionConfig2TD,
    FusionConfig3,
    FusionConfig4,
    InputPaths,
    IOPaths,
    NestedConfigWithVarArgs,
    NestedTypedDictWithVarArgs,
)


def throw_dice(cfg: DieConfig, count: int = 1) -> None:
    """
    Throw dice according to the configuration.

    Args:
        cfg: The configuration for the dice.
        count: The number of dice to throw.
    """
    pass


def throw_dice_union(cfg: DieConfig | str, count: int = 1) -> None:
    """
    Throw dice according to the configuration.

    Args:
        cfg: The configuration for the dice or a string.
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
    cli_args: list[str] = []
    config_kwargs = {}
    if sides is not None:
        cli_args += [sides_opt, str(sides)]
        config_kwargs["sides"] = sides
    if kind is not None:
        cli_args += [kind_opt, kind]
        config_kwargs["kind"] = kind
    if count is not None:
        cli_args += [count_opt, str(count)]

    expected_cfg = DieConfig(**config_kwargs)  # type: ignore[arg-type]
    expected_count = count if count is not None else 1
    check_args(throw_dice, cli_args, [expected_cfg, expected_count], {}, recurse=True)
    with raises(
        ParserConfigError,
        match="Cannot recurse into parameter `cfg` of non-class type `DieConfig | str` in `throw_dice_union()`!",
    ):
        check_args(
            throw_dice_union, cli_args, [expected_cfg, expected_count], {}, recurse=True
        )


@mark.parametrize("count_opt", ["--count", "-c"])
@mark.parametrize("sides", [4, 6, None])
@mark.parametrize("kind", ["single", "pair", None])
@mark.parametrize("count", [1, 2, None])
def test_recursive_w_defaults_nested(
    count_opt: str,
    sides: int | None,
    kind: Literal["single", "pair"] | None,
    count: int | None,
) -> None:
    cli_args: list[str] = []
    config_kwargs = {}
    if sides is not None:
        cli_args += ["--cfg.sides", str(sides)]
        config_kwargs["sides"] = sides
    if kind is not None:
        cli_args += ["--cfg.kind", kind]
        config_kwargs["kind"] = kind
    if count is not None:
        cli_args += [count_opt, str(count)]

    expected_cfg = DieConfig(**config_kwargs)  # type: ignore[arg-type]
    expected_count = count if count is not None else 1
    check_args(
        throw_dice,
        cli_args,
        [expected_cfg, expected_count],
        {},
        recurse=True,
        naming="nested",
    )
    with raises(
        ParserConfigError,
        match="Cannot recurse into parameter `cfg` of non-class type `DieConfig | str` in `throw_dice_union()`!",
    ):
        check_args(
            throw_dice_union,
            cli_args,
            [expected_cfg, expected_count],
            {},
            recurse=True,
            naming="nested",
        )


def throw_dice2(cfg: DieConfig2, count: int) -> None:
    """
    Throw dice according to the configuration.

    Args:
        cfg: The configuration for the dice.
        count: The number of dice to throw.
    """
    pass


def throw_dice2_td(cfg: DieConfig2TD, count: int) -> None:
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
@mark.parametrize("cls", [DieConfig2, DieConfig2TD])
def test_recursive_w_required(
    sides_opt: str,
    kind_opt: str,
    count_opt: str,
    sides: int | None,
    kind: Literal["single", "pair"] | None,
    count: int | None,
    cls: type,
) -> None:
    if cls is DieConfig2:
        func = throw_dice2
    else:
        func = throw_dice2_td
    cli_args: list[str] = []
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
            check_args(func, cli_args, [], {}, recurse=True)
    elif kind is None:
        with raises(ParserOptionError, match="Required option `kind` is not provided!"):
            check_args(func, cli_args, [], {}, recurse=True)
    elif count is None:
        with raises(
            ParserOptionError, match="Required option `count` is not provided!"
        ):
            check_args(func, cli_args, [], {}, recurse=True)
    else:
        expected_cfg: DieConfig2 | dict[str, Any] = (
            DieConfig2(**config_kwargs) if cls is DieConfig2 else {**config_kwargs}  # type: ignore[arg-type]
        )
        expected_count = count
        check_args(func, cli_args, [expected_cfg, expected_count], {}, recurse=True)


@mark.parametrize("count_opt", ["--count", "-c"])
@mark.parametrize("sides", [4, 6, None])
@mark.parametrize("kind", ["single", "pair", None])
@mark.parametrize("count", [1, 2, None])
@mark.parametrize("cls", [DieConfig2, DieConfig2TD])
def test_recursive_w_required_nested(
    count_opt: str,
    sides: int | None,
    kind: Literal["single", "pair"] | None,
    count: int | None,
    cls: type,
) -> None:
    if cls is DieConfig2:
        func = throw_dice2
    else:
        func = throw_dice2_td
    cli_args: list[str] = []
    config_kwargs = {}
    if sides is not None:
        cli_args += ["--cfg.sides", str(sides)]
        config_kwargs["sides"] = sides
    if kind is not None:
        cli_args += ["--cfg.kind", kind]
        config_kwargs["kind"] = kind
    if count is not None:
        cli_args += [count_opt, str(count)]

    if sides is None:
        with raises(
            ParserOptionError, match="Required option `cfg.sides` is not provided!"
        ):
            check_args(func, cli_args, [], {}, recurse=True, naming="nested")
    elif kind is None:
        with raises(
            ParserOptionError, match="Required option `cfg.kind` is not provided!"
        ):
            check_args(func, cli_args, [], {}, recurse=True, naming="nested")
    elif count is None:
        with raises(
            ParserOptionError, match="Required option `count` is not provided!"
        ):
            check_args(func, cli_args, [], {}, recurse=True, naming="nested")
    else:
        expected_cfg: DieConfig2 | dict[str, Any] = (
            DieConfig2(**config_kwargs) if cls is DieConfig2 else {**config_kwargs}  # type: ignore[arg-type]
        )
        expected_count = count
        check_args(
            func,
            cli_args,
            [expected_cfg, expected_count],
            {},
            recurse=True,
            naming="nested",
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

    # Partial provision of child args means the user intended to build the child;
    # missing a required inner arg should surface that, not silently fall back
    # to the parent's default.
    for func in [throw_dice3, throw_dice4]:
        with raises(ParserOptionError, match="Required option `kind` is not provided!"):
            check_args(
                func,
                ["--count", "2", "--sides", "4"],
                [],
                {},
                recurse=True,
            )


def test_recursive_w_inner_required_nested() -> None:
    check_args(
        throw_dice3,
        ["--cfg.sides", "4", "--cfg.kind", "pair", "--count", "2"],
        [2, DieConfig2(sides=4, kind="pair")],
        {},
        recurse=True,
        naming="nested",
    )
    check_args(
        throw_dice4,
        ["--cfg.sides", "4", "--cfg.kind", "pair", "--count", "2"],
        [2, DieConfig2(sides=4, kind="pair")],
        {},
        recurse=True,
        naming="nested",
    )

    # DieConfig2 requires sides and kind, however cfg has a default.
    check_args(
        throw_dice3,
        ["--count", "2"],
        [2, DieConfig2(sides=6, kind="single")],
        {},
        recurse=True,
        naming="nested",
    )
    check_args(
        throw_dice4,
        ["--count", "2"],
        [2, None],
        {},
        recurse=True,
        naming="nested",
    )

    # Partial provision should raise, not silently fall back.
    for func in [throw_dice3, throw_dice4]:
        with raises(
            ParserOptionError, match="Required option `cfg.kind` is not provided!"
        ):
            check_args(
                func,
                ["--count", "2", "--cfg.sides", "4"],
                [],
                {},
                recurse=True,
                naming="nested",
            )


def test_recursive_partial_child_grandchild() -> None:
    """
    Partial provision of a grandchild's args should surface the missing-required
    error at the grandchild level rather than silently dropping every level above.
    """
    from dataclasses import dataclass

    @dataclass
    class Grand:
        grand_req: str
        grand_opt: str = "grand-default"

    @dataclass
    class Middle:
        mid_val: str = "mid-default"
        grand: Grand | None = None

    def run(count: int, mid: Middle | None = None) -> None:
        pass

    # User touches only grand_opt (grandchild is optional, middle is optional,
    # grand_req is required). Should surface the missing required arg.
    with raises(
        ParserOptionError, match="Required option `grand-req` is not provided!"
    ):
        check_args(run, ["--count", "1", "--grand-opt", "X"], [], {}, recurse=True)

    # Control: when no grandchild arg is touched, the existing silent-default
    # behavior for untouched optional subtrees is preserved (middle has only
    # optional fields, so it gets built with defaults and a None grand).
    check_args(
        run,
        ["--count", "1"],
        [1, Middle(mid_val="mid-default", grand=None)],
        {},
        recurse=True,
    )


def test_recursive_branch_does_not_eat_sibling_positional() -> None:
    """
    A recursable branch is a positional-or-keyword param in the Python signature,
    but there's no way to spell a class as a single CLI token. Positional tokens
    from the CLI must flow past the branch to the next real positional leaf /
    variadic.
    """
    from dataclasses import dataclass

    @dataclass
    class Cfg:
        x: int = 0

    # Branch + positional leaf sibling.
    def f1(cfg: Cfg, name: str) -> None:
        pass

    check_args(f1, ["--x=5", "hi"], [Cfg(x=5), "hi"], {}, recurse=True)
    check_args(f1, ["hi", "--x=5"], [Cfg(x=5), "hi"], {}, recurse=True)

    # Branch + *args sibling.
    def f2(cfg: Cfg, *extra: str) -> None:
        pass

    check_args(
        f2, ["--x=5", "a", "b", "c"], [Cfg(x=5), "a", "b", "c"], {}, recurse=True
    )

    # Branch with positional-only leaf sibling.
    def f3(cfg: Cfg, name: str, /) -> None:
        pass

    check_args(f3, ["--x=5", "hi"], [Cfg(x=5), "hi"], {}, recurse=True)


def test_recursive_branch_rejects_direct_value() -> None:
    """
    A recursable branch has no single-token representation — assigning a value
    directly (e.g. `--cfg=foo` or `--cfg foo`) should surface a helpful error,
    not the internal `UnsupportedValueTypeError` that leaks the class type.
    """
    from dataclasses import dataclass

    @dataclass
    class Cfg:
        x: int = 0

    def f(cfg: Cfg) -> None:
        pass

    # flat naming: `cfg` is the branch's name
    with raises(
        ParserOptionError,
        match=r"Option `cfg` takes sub-options, not a direct value!",
    ):
        check_args(f, ["--cfg=foo"], [], {}, recurse=True)
    with raises(
        ParserOptionError,
        match=r"Option `cfg` takes sub-options, not a direct value!",
    ):
        check_args(f, ["--cfg", "foo"], [], {}, recurse=True)

    # nested naming: branch's name is still `cfg` at the top level
    with raises(
        ParserOptionError,
        match=r"Option `cfg` takes sub-options, not a direct value!",
    ):
        check_args(f, ["--cfg=foo"], [], {}, recurse=True, naming="nested")


@mark.parametrize("naming", ["flat", "nested"])
def test_recursive_unsupported(naming: Literal["flat", "nested"]) -> None:
    def f1(cfg: ConfigWithVarArgs) -> None:
        pass

    def f2(cfg: ConfigWithVarKwargs) -> None:
        pass

    def f3(cfg: NestedConfigWithVarArgs) -> None:
        pass

    def f3b(cfg: NestedTypedDictWithVarArgs) -> None:
        pass

    with raises(
        ParserConfigError,
        match="Cannot have variadic parameter `values` in child Args of `ConfigWithVarArgs`!",
    ):
        check_args(f1, [], [], {}, recurse=True, naming=naming)
    with raises(
        ParserConfigError,
        match="Cannot have variadic parameter `settings` in child Args of `ConfigWithVarKwargs`!",
    ):
        check_args(f2, [], [], {}, recurse=True, naming=naming)
    with raises(
        ParserConfigError,
        match="Cannot have variadic parameter `values` in child Args of `ConfigWithVarArgs`!",
    ):
        check_args(f3, [], [], {}, recurse=True, naming=naming)
    with raises(
        ParserConfigError,
        match="Cannot have variadic parameter `values` in child Args of `ConfigWithVarArgs`!",
    ):
        check_args(f3b, [], [], {}, recurse=True, naming=naming)

    def f4a(cfgs: list[DieConfig]) -> None:
        pass

    def f4b(cfgs: list[DieConfig2TD]) -> None:
        pass

    def f5a(*cfgs: DieConfig) -> None:
        pass

    def f5b(*cfgs: DieConfig2TD) -> None:
        pass

    def f6a(**cfgs: DieConfig) -> None:
        pass

    def f6b(**cfgs: DieConfig2TD) -> None:
        pass

    for f in [f4a, f4b]:
        with raises(
            ParserConfigError,
            match=re.escape(
                f"Cannot recurse into n-ary parameter `cfgs` in `{f.__name__}()`!"
            ),
        ):
            check_args(f, [], [], {}, recurse=True, naming=naming)

    for f in [f5a, f5b]:
        with raises(
            ParserConfigError,
            match=re.escape(
                f"Cannot recurse into variadic parameter `cfgs` in `{f.__name__}()`!"
            ),
        ):
            check_args(f, [], [], {}, recurse=True, naming=naming)
    for f in [f6a, f6b]:
        with raises(
            ParserConfigError,
            match=re.escape(
                f"Cannot recurse into variadic parameter `cfgs` in `{f.__name__}()`!"
            ),
        ):
            check_args(f, [], [], {}, recurse=True, naming=naming)

    def f7a(cfg: DieConfig, sides: int) -> None:
        pass

    def f7b(cfg: DieConfig2TD, sides: int) -> None:
        pass

    if naming == "flat":
        for f in [f7a, f7b]:
            with raises(
                ParserConfigError,
                match=re.escape(
                    f"Option name `sides` is used multiple times in `{f.__name__}()`!"
                    " Recursive parsing with `flat` naming requires unique option names among all levels."
                ),
            ):
                check_args(f, [], [], {}, recurse=True)
    else:
        check_args(
            f7a,
            ["--cfg.sides", "4", "--cfg.kind", "pair", "--sides", "8"],
            [DieConfig(sides=4, kind="pair"), 8],
            {},
            recurse=True,
            naming="nested",
        )
        check_args(
            f7b,
            ["--cfg.sides", "4", "--cfg.kind", "pair", "--sides", "8"],
            [{"sides": 4, "kind": "pair"}, 8],
            {},
            recurse=True,
            naming="nested",
        )

    def f8a(cfg: DieConfig, cfg2: DieConfig) -> None:
        pass

    def f8b(cfg: DieConfig, cfg2: DieConfig2TD) -> None:
        pass

    def f8c(cfg: DieConfig2TD, cfg2: DieConfig) -> None:
        pass

    def f8d(cfg: DieConfig2TD, cfg2: DieConfig2TD) -> None:
        pass

    if naming == "flat":
        for f in [f8a, f8b, f8c, f8d]:
            with raises(
                ParserConfigError,
                match=re.escape(
                    f"Option name `sides` is used multiple times in `{f.__name__}()`!"
                    " Recursive parsing with `flat` naming requires unique option names among all levels."
                ),
            ):
                check_args(f, [], [], {}, recurse=True)
    else:
        check_args(
            f8a,
            [
                "--cfg.sides",
                "4",
                "--cfg.kind",
                "pair",
                "--cfg2.sides",
                "8",
                "--cfg2.kind",
                "single",
            ],
            [DieConfig(sides=4, kind="pair"), DieConfig(sides=8, kind="single")],
            {},
            recurse=True,
            naming="nested",
        )
        check_args(
            f8b,
            [
                "--cfg.sides",
                "4",
                "--cfg.kind",
                "pair",
                "--cfg2.sides",
                "8",
                "--cfg2.kind",
                "single",
            ],
            [DieConfig(sides=4, kind="pair"), {"sides": 8, "kind": "single"}],
            {},
            recurse=True,
            naming="nested",
        )
        check_args(
            f8c,
            [
                "--cfg.sides",
                "4",
                "--cfg.kind",
                "pair",
                "--cfg2.sides",
                "8",
                "--cfg2.kind",
                "single",
            ],
            [{"sides": 4, "kind": "pair"}, DieConfig(sides=8, kind="single")],
            {},
            recurse=True,
            naming="nested",
        )
        check_args(
            f8d,
            [
                "--cfg.sides",
                "4",
                "--cfg.kind",
                "pair",
                "--cfg2.sides",
                "8",
                "--cfg2.kind",
                "single",
            ],
            [{"sides": 4, "kind": "pair"}, {"sides": 8, "kind": "single"}],
            {},
            recurse=True,
            naming="nested",
        )


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


def fuse2td(cfg: FusionConfig2TD) -> None:
    """
    Fuse two monsters with polymerization.

    Args:
        cfg: The fusion configuration.
    """
    pass


@mark.parametrize("fuse", [fuse1, fuse2, fuse2td])
def test_recursive_dataclass_help(fuse: Callable[..., Any]) -> None:
    if fuse is fuse1:
        expected = FusionConfig(
            left_path="monster1.dat",
            right_path="monster2.dat",
            output_path="fused_monster.dat",
            components=["wing", "tail"],
            alpha=0.7,
        )
    elif fuse is fuse2:
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
    else:
        expected = {
            "io_paths": IOPaths(
                input_paths=InputPaths(
                    left_path="monster1.dat", right_path="monster2.dat"
                ),
                output_path="fused_monster.dat",
            ),
            "components": ["wing", "tail"],
            "alpha": 0.7,
        }
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
  fuse.py [{NS} {OS}]--left-path[/] [{VS}]<text>[/] [{NS} {OS}]--right-path[/] [{VS}]<text>[/] [{NS} {OS}]--output-path[/] [{VS}]<text>[/] [[{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]]
          [[{NS} {OS}]--alpha[/] [{VS}]<float>[/]]

[{TS}]where[/]
  [dim](option)[/]  [{NS} {OS}]-l[/][{OS} dim]|[/][{NS} {OS}]--left-path[/] [{VS}]<text>[/]                [i]Path to the first monster.[/] [yellow](required)[/]                 
  [dim](option)[/]  [{NS} {OS}]-r[/][{OS} dim]|[/][{NS} {OS}]--right-path[/] [{VS}]<text>[/]               [i]Path to the second monster.[/] [yellow](required)[/]                
  [dim](option)[/]  [{NS} {OS}]-p[/][{OS} dim]|[/][{NS} {OS}]--output-path[/] [{VS}]<text>[/]              [i]Path to store the fused monster.[/] [yellow](required)[/]           
  [dim](option)[/]  [{NS} {OS}]-c[/][{OS} dim]|[/][{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]  [i]Components to fuse.[/] [green](default: [/][green]['fang', 'claw'][/][green])[/]       
  [dim](option)[/]  [{NS} {OS}]-a[/][{OS} dim]|[/][{NS} {OS}]--alpha[/] [{VS}]<float>[/]                   [i]Weighting factor for the first monster.[/] [green](default: [/][green]0.5[/][green])[/]
  [dim](option)[/]  [{NS} {OS} dim]-?[/][{OS} dim]|[/][{NS} {OS} dim]--help[/]                            [i dim]Show this help message and exit.[/]                      
"""
    if fuse is not fuse2td:
        # TypedDict example does not have default values, every option is required.
        check_help_from_func(fuse, "fuse.py", expected, recurse=True)


@mark.parametrize("fuse", [fuse2, fuse2td])
def test_recursive_dataclass_nested(fuse: Callable[..., Any]) -> None:
    if fuse is fuse2:
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
    else:
        expected = {
            "io_paths": IOPaths(
                input_paths=InputPaths(
                    left_path="monster1.dat", right_path="monster2.dat"
                ),
                output_path="fused_monster.dat",
            ),
            "components": ["wing", "tail"],
            "alpha": 0.7,
        }
    check_args(
        fuse,
        [
            "--cfg.io-paths.input-paths.left-path",
            "monster1.dat",
            "--cfg.io-paths.input-paths.right-path",
            "monster2.dat",
            "--cfg.io-paths.output-path",
            "fused_monster.dat",
            "--cfg.components",
            "wing",
            "tail",
            "--cfg.alpha",
            "0.7",
        ],
        [expected],
        {},
        recurse=True,
        naming="nested",
    )


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
  fuse.py [{NS} {OS}]--left-path[/] [{VS}]<text>[/] [{NS} {OS}]--right-path[/] [{VS}]<text>[/] [{NS} {OS}]--output-path[/] [{VS}]<text>[/] [[{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]]
          [[{NS} {OS}]--alpha[/] [{VS}]<float>[/]]

[{TS}]where[/]
  [dim](option)[/]  [{NS} {OS}]--left-path[/] [{VS}]<text>[/]                   [i]Path to the first monster.[/] [yellow](required)[/]                 
  [dim](option)[/]  [{NS} {OS}]-r[/][{OS} dim]|[/][{NS} {OS}]--right-path[/] [{VS}]<text>[/]               [i]Path to the second monster.[/] [yellow](required)[/]                
  [dim](option)[/]  [{NS} {OS}]-l[/][{OS} dim]|[/][{NS} {OS}]--output-path[/] [{VS}]<text>[/]              [i]Path to store the fused monster.[/] [yellow](required)[/]           
  [dim](option)[/]  [{NS} {OS}]-c[/][{OS} dim]|[/][{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]  [i]Components to fuse.[/] [green](default: [/][green]['fang', 'claw'][/][green])[/]       
  [dim](option)[/]  [{NS} {OS}]-a[/][{OS} dim]|[/][{NS} {OS}]--alpha[/] [{VS}]<float>[/]                   [i]Weighting factor for the first monster.[/] [green](default: [/][green]0.5[/][green])[/]
  [dim](option)[/]  [{NS} {OS} dim]-?[/][{OS} dim]|[/][{NS} {OS} dim]--help[/]                            [i dim]Show this help message and exit.[/]                      
"""
    check_help_from_func(fuse3, "fuse.py", expected, recurse=True)


def fuse4(cfg: FusionConfig4) -> None:
    """
    Fuse two monsters with polymerization.

    Args:
        cfg: The fusion configuration.
    """
    pass


def test_recursive_dataclass_non_class() -> None:
    with raises(
        ParserConfigError,
        match="Cannot recurse into parameter `io_paths` of non-class type `IOPaths2 | tuple[str, str]` in `fuse4()`!",
    ):
        check_help_from_func(fuse4, "fuse.py", "", recurse=True)


def make_fruit_salad(
    apple_cfg: AppleConfig,
    banana_cfg: BananaConfig,
    servings: int = 1,
) -> None:
    """
    Make a fruit salad.

    Args:
        apple_cfg: Configuration for the apple.
        banana_cfg: Configuration for the banana.
        servings: Number of servings.
    """
    pass


@mark.parametrize(
    "cli_args",
    [
        ["--color", "green", "--heavy", "--length", "7.5", "--ripe", "--servings", "3"],
        ["--color", "green", "--length", "7.5", "-h", "-r", "-s", "3"],
        ["--color", "green", "--length", "7.5", "-hrs", "3"],
        ["--color", "green", "--length", "7.5", "-hrs=3"],
        ["--color", "green", "--length", "7.5", "-rhs", "3"],
        ["--color", "green", "--length", "7.5", "-rhs=3"],
    ],
)
def test_combined_short_flags(cli_args: list[str]) -> None:
    check_args(
        make_fruit_salad,
        cli_args,
        [
            AppleConfig(color="green", heavy=True),
            BananaConfig(length=7.5, ripe=True),
            3,
        ],
        {},
        recurse=True,
    )
