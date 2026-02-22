from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict

from pytest import mark, raises
from startle import parse
from startle.error import ParserConfigError, ParserOptionError


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
