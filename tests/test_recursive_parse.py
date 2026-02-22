import re
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict

from pytest import mark, raises
from startle import parse
from startle.error import ParserConfigError, ParserOptionError

from .test_help._utils import (
    NS,
    OS,
    TS,
    VS,
    check_help_from_class,
)


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


@dataclass
class MainConfig:
    """
    Main configuration for the dice program.

    Attributes:
        cfg: The configuration for the dice.
        count: The number of dice to throw.
    """

    cfg: DieConfig
    count: int = 1


@dataclass
class MainConfigUnion:
    """
    Main configuration for the dice program.

    Attributes:
        cfg: The configuration for the dice or a string.
        count: The number of dice to throw.
    """

    cfg: DieConfig | str
    count: int = 1


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

    # expected_cfg = DieConfig(**config_kwargs)  # type: ignore[arg-type]
    # expected_count = count if count is not None else 1
    cfg = parse(MainConfig, args=cli_args, recurse=True)

    assert cfg == MainConfig(
        cfg=DieConfig(**config_kwargs),  # type: ignore[arg-type]
        count=count if count is not None else 1,
    )

    with raises(
        ParserConfigError,
        match="Cannot recurse into parameter `cfg` of non-class type `DieConfig | str` in `MainConfigUnion`!",
    ):
        parse(MainConfigUnion, args=cli_args, recurse=True)


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

    cfg = parse(MainConfig, args=cli_args, recurse=True, naming="nested")
    assert cfg == MainConfig(
        cfg=DieConfig(**config_kwargs),  # type: ignore[arg-type]
        count=count if count is not None else 1,
    )

    with raises(
        ParserConfigError,
        match="Cannot recurse into parameter `cfg` of non-class type `DieConfig | str` in `MainConfigUnion`!",
    ):
        parse(MainConfigUnion, args=cli_args, recurse=True, naming="nested")


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


@dataclass
class MainConfig2:
    """
    Main configuration for the dice program.

    Attributes:
        cfg: The configuration for the dice.
        count: The number of dice to throw.
    """

    cfg: DieConfig2
    count: int


class DieConfig2TD(TypedDict):
    """
    Configuration for the dice program.

    Attributes:
        sides: The number of sides on the dice.
        kind: Whether to throw a single die or a pair of dice.
    """

    sides: int
    kind: Literal["single", "pair"]


@dataclass
class MainConfig2TD:
    """
    Main configuration for the dice program.

    Attributes:
        cfg: The configuration for the dice.
        count: The number of dice to throw.
    """

    cfg: DieConfig2TD
    count: int


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
        outer = MainConfig2
    else:
        outer = MainConfig2TD
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
            parse(outer, args=cli_args, recurse=True, catch=False)
    elif kind is None:
        with raises(ParserOptionError, match="Required option `kind` is not provided!"):
            parse(outer, args=cli_args, recurse=True, catch=False)
    elif count is None:
        with raises(
            ParserOptionError, match="Required option `count` is not provided!"
        ):
            parse(outer, args=cli_args, recurse=True, catch=False)
    else:
        cfg = parse(outer, args=cli_args, recurse=True)
        expected_inner_cfg: DieConfig2 | dict[str, Any] = (
            DieConfig2(**config_kwargs) if cls is DieConfig2 else {**config_kwargs}  # type: ignore[arg-type]
        )
        expected_count = count
        assert cfg == outer(
            cfg=expected_inner_cfg,  # type: ignore[arg-type]
            count=expected_count,
        )


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
        outer = MainConfig2
    else:
        outer = MainConfig2TD
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
            parse(outer, args=cli_args, recurse=True, naming="nested", catch=False)
    elif kind is None:
        with raises(
            ParserOptionError, match="Required option `cfg.kind` is not provided!"
        ):
            parse(outer, args=cli_args, recurse=True, naming="nested", catch=False)
    elif count is None:
        with raises(
            ParserOptionError, match="Required option `count` is not provided!"
        ):
            parse(outer, args=cli_args, recurse=True, naming="nested", catch=False)
    else:
        expected_cfg: DieConfig2 | dict[str, Any] = (
            DieConfig2(**config_kwargs) if cls is DieConfig2 else {**config_kwargs}  # type: ignore[arg-type]
        )
        expected_count = count
        cfg = parse(outer, args=cli_args, recurse=True, naming="nested")
        assert cfg == outer(
            cfg=expected_cfg,  # type: ignore[arg-type]
            count=expected_count,
        )


@dataclass
class MainConfig3:
    """
    Main configuration for the dice program.

    Attributes:
        count: The number of dice to throw.
        cfg: The configuration for the dice.
    """

    count: int
    cfg: DieConfig2 = field(default_factory=lambda: DieConfig2(sides=6, kind="single"))


@dataclass
class MainConfig4:
    """
    Main configuration for the dice program.

    Attributes:
        count: The number of dice to throw.
        cfg: The configuration for the dice.
    """

    count: int
    cfg: DieConfig2 | None = None


def test_recursive_w_inner_required() -> None:
    cfg = parse(
        MainConfig3,
        args=["--sides", "4", "--kind", "pair", "--count", "2"],
        recurse=True,
        catch=False,
    )
    assert cfg == MainConfig3(count=2, cfg=DieConfig2(sides=4, kind="pair"))

    cfg = parse(
        MainConfig4,
        args=["--sides", "4", "--kind", "pair", "--count", "2"],
        recurse=True,
        catch=False,
    )
    assert cfg == MainConfig4(count=2, cfg=DieConfig2(sides=4, kind="pair"))

    # DieConfig2 requires sides and kind, however cfg has a default.
    cfg = parse(
        MainConfig3,
        args=["--count", "2"],
        recurse=True,
        catch=False,
    )
    assert cfg == MainConfig3(count=2, cfg=DieConfig2(sides=6, kind="single"))

    cfg = parse(
        MainConfig4,
        args=["--count", "2"],
        recurse=True,
        catch=False,
    )
    assert cfg == MainConfig4(count=2, cfg=None)


def test_recursive_w_inner_required_nested() -> None:
    cfg = parse(
        MainConfig3,
        args=["--cfg.sides", "4", "--cfg.kind", "pair", "--count", "2"],
        recurse=True,
        naming="nested",
        catch=False,
    )
    assert cfg == MainConfig3(count=2, cfg=DieConfig2(sides=4, kind="pair"))

    cfg = parse(
        MainConfig4,
        args=["--cfg.sides", "4", "--cfg.kind", "pair", "--count", "2"],
        recurse=True,
        naming="nested",
        catch=False,
    )
    assert cfg == MainConfig4(count=2, cfg=DieConfig2(sides=4, kind="pair"))

    # DieConfig2 requires sides and kind, however cfg has a default.
    cfg = parse(
        MainConfig3,
        args=["--count", "2"],
        recurse=True,
        naming="nested",
        catch=False,
    )
    assert cfg == MainConfig3(count=2, cfg=DieConfig2(sides=6, kind="single"))

    cfg = parse(
        MainConfig4,
        args=["--count", "2"],
        recurse=True,
        naming="nested",
        catch=False,
    )
    assert cfg == MainConfig4(count=2, cfg=None)


class ConfigWithVarArgs:
    def __init__(self, *values: int) -> None:
        self.values = list(values)


class ConfigWithVarKwargs:
    def __init__(self, **settings: int) -> None:
        self.settings = settings


@dataclass
class NestedConfigWithVarArgs:
    config: ConfigWithVarArgs


class NestedTypedDictWithVarArgs(TypedDict):
    config: ConfigWithVarArgs


@mark.parametrize("naming", ["flat", "nested"])
def test_recursive_unsupported(naming: Literal["flat", "nested"]) -> None:
    @dataclass
    class C1:
        cfg: ConfigWithVarArgs

    @dataclass
    class C2:
        cfg: ConfigWithVarKwargs

    @dataclass
    class C3:
        cfg: NestedConfigWithVarArgs

    @dataclass
    class C4:
        cfg: NestedTypedDictWithVarArgs

    with raises(
        ParserConfigError,
        match="Cannot have variadic parameter `values` in child Args of `ConfigWithVarArgs`!",
    ):
        parse(C1, args=[], recurse=True, naming=naming)
    with raises(
        ParserConfigError,
        match="Cannot have variadic parameter `settings` in child Args of `ConfigWithVarKwargs`!",
    ):
        parse(C2, args=[], recurse=True, naming=naming)
    with raises(
        ParserConfigError,
        match="Cannot have variadic parameter `values` in child Args of `ConfigWithVarArgs`!",
    ):
        parse(C3, args=[], recurse=True, naming=naming)
    with raises(
        ParserConfigError,
        match="Cannot have variadic parameter `values` in child Args of `ConfigWithVarArgs`!",
    ):
        parse(C4, args=[], recurse=True, naming=naming)

    @dataclass
    class C4a:
        cfgs: list[DieConfig]

    @dataclass
    class C4b:
        cfgs: list[DieConfig2TD]

    for cls in [C4a, C4b]:
        with raises(
            ParserConfigError,
            match=f"Cannot recurse into n-ary parameter `cfgs` in `{cls.__name__}`!",
        ):
            parse(cls, args=[], recurse=True, naming=naming)

    @dataclass
    class C5a:
        cfg: DieConfig
        sides: int

    @dataclass
    class C5b:
        cfg: DieConfig2TD
        sides: int

    if naming == "flat":
        for cls in [C5a, C5b]:
            with raises(
                ParserConfigError,
                match=re.escape(
                    f"Option name `sides` is used multiple times in `{cls.__name__}`!"
                    " Recursive parsing with `flat` naming requires unique option names among all levels."
                ),
            ):
                parse(cls, args=[], recurse=True, naming=naming)
    else:
        cfg = parse(
            C5a,
            args=["--cfg.sides", "4", "--cfg.kind", "single", "--sides", "8"],
            recurse=True,
            naming=naming,
        )
        assert cfg == C5a(cfg=DieConfig(sides=4, kind="single"), sides=8)

        cfg = parse(
            C5b,
            args=["--cfg.sides", "4", "--cfg.kind", "single", "--sides", "8"],
            recurse=True,
            naming=naming,
        )
        assert cfg == C5b(cfg={"sides": 4, "kind": "single"}, sides=8)

    @dataclass
    class C6a:
        cfg: DieConfig
        cfg2: DieConfig

    @dataclass
    class C6b:
        cfg: DieConfig
        cfg2: DieConfig2TD

    @dataclass
    class C6c:
        cfg: DieConfig2TD
        cfg2: DieConfig

    @dataclass
    class C6d:
        cfg: DieConfig2TD
        cfg2: DieConfig2TD

    if naming == "flat":
        for cls in [C6a, C6b, C6c, C6d]:
            with raises(
                ParserConfigError,
                match=re.escape(
                    f"Option name `sides` is used multiple times in `{cls.__name__}`!"
                    " Recursive parsing with `flat` naming requires unique option names among all levels."
                ),
            ):
                parse(cls, args=[], recurse=True, naming=naming)
    else:
        cfg = parse(
            C6a,
            args=[
                "--cfg.sides",
                "4",
                "--cfg.kind",
                "pair",
                "--cfg2.sides",
                "8",
                "--cfg2.kind",
                "single",
            ],
            recurse=True,
            naming="nested",
        )
        assert cfg == C6a(
            cfg=DieConfig(sides=4, kind="pair"),
            cfg2=DieConfig(sides=8, kind="single"),
        )

        cfg = parse(
            C6b,
            args=[
                "--cfg.sides",
                "4",
                "--cfg.kind",
                "pair",
                "--cfg2.sides",
                "8",
                "--cfg2.kind",
                "single",
            ],
            recurse=True,
            naming="nested",
        )
        assert cfg == C6b(
            cfg=DieConfig(sides=4, kind="pair"),
            cfg2={"sides": 8, "kind": "single"},
        )

        cfg = parse(
            C6c,
            args=[
                "--cfg.sides",
                "4",
                "--cfg.kind",
                "pair",
                "--cfg2.sides",
                "8",
                "--cfg2.kind",
                "single",
            ],
            recurse=True,
            naming="nested",
        )
        assert cfg == C6c(
            cfg={"sides": 4, "kind": "pair"},
            cfg2=DieConfig(sides=8, kind="single"),
        )

        cfg = parse(
            C6d,
            args=[
                "--cfg.sides",
                "4",
                "--cfg.kind",
                "pair",
                "--cfg2.sides",
                "8",
                "--cfg2.kind",
                "single",
            ],
            recurse=True,
            naming="nested",
        )
        assert cfg == C6d(
            cfg={"sides": 4, "kind": "pair"},
            cfg2={"sides": 8, "kind": "single"},
        )


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


class FusionConfig2TD(TypedDict):
    """
    Fusion config with separate input and output paths.

    Attributes:
        io_paths: Input and output paths for the fusion.
        components: Components to fuse.
        alpha: Weighting factor for the first monster.
    """

    io_paths: IOPaths
    components: list[str]
    alpha: float


def fuse1(cfg: FusionConfig) -> None:
    """
    Fuse two monsters with polymerization.

    Args:
        cfg: The fusion configuration.
    """
    pass


@dataclass
class Fuse1:
    """
    Top level fusion config.

    Attributes:
        cfg: The fusion configuration.
    """

    cfg: FusionConfig


@dataclass
class Fuse2:
    """
    Top level fusion config.

    Attributes:
        cfg: The fusion configuration.
    """

    cfg: FusionConfig2


@dataclass
class Fuse2TD:
    """
    Top level fusion config.

    Attributes:
        cfg: The fusion configuration.
    """

    cfg: FusionConfig2TD


@mark.parametrize("cls", [Fuse1, Fuse2, Fuse2TD])
def test_recursive_dataclass_help(
    cls: type[Fuse1] | type[Fuse2] | type[Fuse2TD],
) -> None:
    if cls is Fuse1:
        expected = Fuse1(
            FusionConfig(
                left_path="monster1.dat",
                right_path="monster2.dat",
                output_path="fused_monster.dat",
                components=["wing", "tail"],
                alpha=0.7,
            )
        )
    elif cls is Fuse2:
        expected = Fuse2(
            FusionConfig2(
                io_paths=IOPaths(
                    input_paths=InputPaths(
                        left_path="monster1.dat", right_path="monster2.dat"
                    ),
                    output_path="fused_monster.dat",
                ),
                components=["wing", "tail"],
                alpha=0.7,
            )
        )
    else:
        expected = Fuse2TD({
            "io_paths": IOPaths(
                input_paths=InputPaths(
                    left_path="monster1.dat", right_path="monster2.dat"
                ),
                output_path="fused_monster.dat",
            ),
            "components": ["wing", "tail"],
            "alpha": 0.7,
        })

    parsed = parse(
        cls,
        args=[
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
        recurse=True,
        catch=False,
    )
    assert parsed == expected

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

    if cls is not Fuse2TD:
        # TypedDict example does not have default values, every option is required.
        check_help_from_class(
            cls,
            brief="Fuse two monsters with polymerization.",
            program_name="fuse.py",
            expected=expected,
            recurse=True,
        )
