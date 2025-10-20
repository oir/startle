# ruff: noqa: E741

import re
from dataclasses import dataclass
from typing import Annotated, Callable, TypedDict

from pytest import mark, raises
from startle import parse
from startle.error import ParserConfigError, ParserOptionError, ParserValueError


@dataclass
class ConfigDataClass:
    """
    A configuration class for the program.
    """

    count: int = 1
    amount: float = 1.0
    label: str = "default"


class ConfigClass:
    """
    A configuration class for the program.
    """

    def __init__(self, count: int = 1, amount: float = 1.0, label: str = "default"):
        self.count = count
        self.amount = amount
        self.label = label

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConfigClass):
            raise NotImplementedError()
        return (
            self.count == other.count
            and self.amount == other.amount
            and self.label == other.label
        )


@dataclass
class ConfigDataClassAnnotated:
    """
    A configuration class for the program.
    """

    count: int = 1
    amount: Annotated[float, "some metadata"] = 1.0
    label: Annotated[str, "some metadata"] = "default"


def check_parse_exits(capsys, cls: type, args: list[str], expected: str) -> None:
    with raises(SystemExit) as excinfo:
        parse(cls, args=args)
    assert str(excinfo.value) == "1"
    captured = capsys.readouterr()
    assert captured.out.startswith(expected)


@mark.parametrize(
    "count",
    [
        lambda c: ["--count", f"{c}"],
        lambda c: [f"--count={c}"],
        lambda c: ["-c", f"{c}"],
        lambda c: [f"-c={c}"],
    ],
)
@mark.parametrize(
    "amount",
    [
        lambda a: ["--amount", f"{a}"],
        lambda a: [f"--amount={a}"],
        lambda a: ["-a", f"{a}"],
        lambda a: [f"-a={a}"],
    ],
)
@mark.parametrize(
    "label",
    [
        lambda l: ["--label", f"{l}"],
        lambda l: [f"--label={l}"],
        lambda l: ["-l", f"{l}"],
        lambda l: [f"-l={l}"],
    ],
)
@mark.parametrize("Config", [ConfigDataClass, ConfigClass, ConfigDataClassAnnotated])
def test_class_with_all_defaults(
    capsys,
    count: Callable[[str], list[str]],
    amount: Callable[[str], list[str]],
    label: Callable[[str], list[str]],
    Config: type,
):
    assert parse(Config, args=[]) == Config()

    assert parse(Config, args=[*count("2")]) == Config(count=2)
    assert parse(Config, args=["2"]) == Config(count=2)
    assert parse(Config, args=[*amount("2.0")]) == Config(amount=2.0)
    assert parse(Config, args=[*label("custom")]) == Config(label="custom")

    # only count and amount
    assert parse(Config, args=[*count("2"), *amount("2.0")]) == Config(
        count=2, amount=2.0
    )
    assert parse(Config, args=["2", *amount("2.0")]) == Config(count=2, amount=2.0)
    assert parse(Config, args=[*amount("2.0"), "2"]) == Config(count=2, amount=2.0)
    assert parse(Config, args=["2", "2.0"]) == Config(count=2, amount=2.0)

    # only count and label
    expected = Config(count=2, label="custom")
    assert parse(Config, args=[*count("2"), *label("custom")]) == expected
    assert parse(Config, args=[*label("custom"), "2"]) == expected
    assert parse(Config, args=["2", *label("custom")]) == expected
    assert parse(Config, args=[*label("custom"), "2"]) == expected

    # only amount and label
    expected = Config(amount=2.0, label="custom")
    assert parse(Config, args=[*amount("2.0"), *label("custom")]) == expected
    assert parse(Config, args=[*label("custom"), *amount("2.0")]) == expected

    # all three
    expected = Config(count=2, amount=2.0, label="custom")
    assert (
        parse(Config, args=[*count("2"), *amount("2.0"), *label("custom")]) == expected
    )
    assert (
        parse(Config, args=[*count("2"), *label("custom"), *amount("2.0")]) == expected
    )
    assert (
        parse(Config, args=[*amount("2.0"), *label("custom"), *count("2")]) == expected
    )
    assert (
        parse(Config, args=[*amount("2.0"), *count("2"), *label("custom")]) == expected
    )
    assert (
        parse(Config, args=[*label("custom"), *count("2"), *amount("2.0")]) == expected
    )
    assert (
        parse(Config, args=[*label("custom"), *amount("2.0"), *count("2")]) == expected
    )
    assert parse(Config, args=["2", *amount("2.0"), *label("custom")]) == expected
    assert parse(Config, args=[*amount("2.0"), "2", *label("custom")]) == expected
    assert parse(Config, args=[*amount("2.0"), *label("custom"), "2"]) == expected
    assert parse(Config, args=["2", "2.0", *label("custom")]) == expected
    assert parse(Config, args=["2", *label("custom"), "2.0"]) == expected
    assert parse(Config, args=[*label("custom"), "2", "2.0"]) == expected
    assert parse(Config, args=["2", "2.0", "custom"]) == expected

    with raises(ParserOptionError, match="Unexpected option `unknown`!"):
        parse(Config, args=["--unknown"], catch=False)
    with raises(ParserValueError, match="Cannot parse integer from `a`!"):
        parse(Config, args=["a"], catch=False)
    with raises(ParserValueError, match="Cannot parse float from `a`!"):
        parse(Config, args=["2", "a"], catch=False)
    with raises(ParserOptionError, match="Option `count` is missing argument!"):
        parse(Config, args=["--count"], catch=False)
    with raises(ParserOptionError, match="Option `count` is missing argument!"):
        parse(Config, args=["--amount", "1.0", "--count"], catch=False)
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        parse(Config, args=["--count", "2", "--count", "3"], catch=False)

    check_parse_exits(
        capsys, Config, ["--unknown"], "Error: Unexpected option `unknown`!\n"
    )
    check_parse_exits(capsys, Config, ["a"], "Error: Cannot parse integer from `a`!\n")
    check_parse_exits(
        capsys, Config, ["2", "a"], "Error: Cannot parse float from `a`!\n"
    )
    check_parse_exits(
        capsys, Config, ["--count"], "Error: Option `count` is missing argument!\n"
    )
    check_parse_exits(
        capsys,
        Config,
        ["--amount", "1.0", "--count"],
        "Error: Option `count` is missing argument!\n",
    )
    check_parse_exits(
        capsys,
        Config,
        ["--count", "2", "--count", "3"],
        "Error: Option `count` is multiply given!\n",
    )


def test_dataclass_with_help_attr(capsys):
    @dataclass
    class Config:
        """
        A configuration class for the program.
        """

        count: int
        amount: float
        help: str

    with raises(
        ParserConfigError, match="Cannot use `help` as parameter name in `Config`!"
    ):
        parse(Config, args=[], catch=False)
    check_parse_exits(
        capsys, Config, [], "Error: Cannot use `help` as parameter name in `Config`!\n"
    )


def test_dataclass_with_unsupported_attr_type(capsys):
    @dataclass
    class Config:
        """
        A configuration class for the program.
        """

        count: int
        amount: float
        label: list[list[int]]

    with raises(
        ParserConfigError,
        match=re.escape(
            "Unsupported type `list[list[int]]` for parameter `label` in `Config`!"
        ),
    ):
        parse(Config, args=[], catch=False)
    check_parse_exits(
        capsys,
        Config,
        [],
        "Error: Unsupported type `list[list[int]]` for parameter `label` in `Config`!\n",
    )


class ConfigTypedDict(TypedDict):
    """
    A configuration dict for the program.
    """

    count: int
    amount: float
    label: str


class ConfigTypedDictAnnotated(TypedDict):
    """
    A configuration dict for the program.
    """

    count: Annotated[int, "some metadata"]
    amount: Annotated[float, "some metadata"]
    label: Annotated[str, "some metadata"]


@mark.parametrize(
    "count",
    [
        lambda c: ["--count", f"{c}"],
        lambda c: [f"--count={c}"],
        lambda c: ["-c", f"{c}"],
        lambda c: [f"-c={c}"],
    ],
)
@mark.parametrize(
    "amount",
    [
        lambda a: ["--amount", f"{a}"],
        lambda a: [f"--amount={a}"],
        lambda a: ["-a", f"{a}"],
        lambda a: [f"-a={a}"],
    ],
)
@mark.parametrize(
    "label",
    [
        lambda l: ["--label", f"{l}"],
        lambda l: [f"--label={l}"],
        lambda l: ["-l", f"{l}"],
        lambda l: [f"-l={l}"],
    ],
)
@mark.parametrize("cls", [ConfigTypedDict, ConfigTypedDictAnnotated])
def test_typed_dict_config(
    capsys,
    count: Callable[[str], list[str]],
    amount: Callable[[str], list[str]],
    label: Callable[[str], list[str]],
    cls: type,
):
    assert parse(cls, args=[*count("2"), *amount("2.0"), *label("custom")]) == {
        "count": 2,
        "amount": 2.0,
        "label": "custom",
    }


def test_typeddict_with_help_attr(capsys):
    class Config(TypedDict):
        """
        A configuration dict for the program.
        """

        count: int
        amount: float
        help: str

    with raises(
        ParserConfigError, match="Cannot use `help` as parameter name in `Config`!"
    ):
        parse(Config, args=[], catch=False)
    check_parse_exits(
        capsys, Config, [], "Error: Cannot use `help` as parameter name in `Config`!\n"
    )
