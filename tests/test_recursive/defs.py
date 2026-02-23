from dataclasses import dataclass, field
from typing import Literal, TypedDict


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
class DieConfig2:
    """
    Configuration for the dice program.

    Attributes:
        sides: The number of sides on the dice.
        kind: Whether to throw a single die or a pair of dice.
    """

    sides: int
    kind: Literal["single", "pair"]


class DieConfig2TD(TypedDict):
    """
    Configuration for the dice program.

    Attributes:
        sides: The number of sides on the dice.
        kind: Whether to throw a single die or a pair of dice.
    """

    sides: int
    kind: Literal["single", "pair"]


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


@dataclass
class FusionConfig4:
    """
    Fusion config with separate input and output paths.

    Attributes:
        io_paths: Input and output paths for the fusion.
        components: Components to fuse.
        alpha: Weighting factor for the first monster.
    """

    io_paths: IOPaths2 | tuple[str, str]
    components: list[str] = field(default_factory=lambda: ["fang", "claw"])
    alpha: float = 0.5


@dataclass(kw_only=True)
class AppleConfig:
    """
    Configuration for apple.

    Attributes:
        color: The color of the apple.
        heavy: Whether the apple is heavy.
    """

    color: str = "red"
    heavy: bool = False


@dataclass(kw_only=True)
class BananaConfig:
    """
    Configuration for banana.

    Attributes:
        length: The length of the banana.
        ripe: Whether the banana is ripe.
    """

    length: float = 6.0
    ripe: bool = False
