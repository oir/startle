# ruff: noqa: E741

import re
from dataclasses import dataclass
from typing import Callable

from pytest import mark, raises

from startle import parse
from startle.error import ParserConfigError, ParserOptionError, ParserValueError


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
def test_dataclass_with_all_defaults(
    count: Callable[[str], list[str]],
    amount: Callable[[str], list[str]],
    label: Callable[[str], list[str]],
):
    @dataclass
    class Config:
        """
        A configuration class for the program.
        """

        count: int = 1
        amount: float = 1.0
        label: str = "default"

    assert parse(Config, []) == Config()

    assert parse(Config, [*count(2)]) == Config(count=2)
    assert parse(Config, ["2"]) == Config(count=2)
    assert parse(Config, [*amount(2.0)]) == Config(amount=2.0)
    assert parse(Config, [*label("custom")]) == Config(label="custom")

    # only count and amount
    assert parse(Config, [*count(2), *amount(2.0)]) == Config(count=2, amount=2.0)
    assert parse(Config, ["2", *amount(2.0)]) == Config(count=2, amount=2.0)
    assert parse(Config, [*amount(2.0), "2"]) == Config(count=2, amount=2.0)
    assert parse(Config, ["2", "2.0"]) == Config(count=2, amount=2.0)

    # only count and label
    expected = Config(count=2, label="custom")
    assert parse(Config, [*count(2), *label("custom")]) == expected
    assert parse(Config, [*label("custom"), "2"]) == expected
    assert parse(Config, ["2", *label("custom")]) == expected
    assert parse(Config, [*label("custom"), "2"]) == expected

    # only amount and label
    expected = Config(amount=2.0, label="custom")
    assert parse(Config, [*amount(2.0), *label("custom")]) == expected
    assert parse(Config, [*label("custom"), *amount(2.0)]) == expected

    # all three
    expected = Config(count=2, amount=2.0, label="custom")
    assert parse(Config, [*count(2), *amount(2.0), *label("custom")]) == expected
    assert parse(Config, [*count(2), *label("custom"), *amount(2.0)]) == expected
    assert parse(Config, [*amount(2.0), *label("custom"), *count(2)]) == expected
    assert parse(Config, [*amount(2.0), *count(2), *label("custom")]) == expected
    assert parse(Config, [*label("custom"), *count(2), *amount(2.0)]) == expected
    assert parse(Config, [*label("custom"), *amount(2.0), *count(2)]) == expected
    assert parse(Config, ["2", *amount(2.0), *label("custom")]) == expected
    assert parse(Config, [*amount(2.0), "2", *label("custom")]) == expected
    assert parse(Config, [*amount(2.0), *label("custom"), "2"]) == expected
    assert parse(Config, ["2", "2.0", *label("custom")]) == expected
    assert parse(Config, ["2", *label("custom"), "2.0"]) == expected
    assert parse(Config, [*label("custom"), "2", "2.0"]) == expected
    assert parse(Config, ["2", "2.0", "custom"]) == expected

    with raises(ParserOptionError, match="Unexpected option `unknown`!"):
        parse(Config, ["--unknown"], caught=False)
    with raises(ParserValueError, match="Cannot parse integer from `a`!"):
        parse(Config, ["a"], caught=False)
    with raises(ParserValueError, match="Cannot parse float from `a`!"):
        parse(Config, ["2", "a"], caught=False)
    with raises(ParserOptionError, match="Option `count` is missing argument!"):
        parse(Config, ["--count"], caught=False)
    with raises(ParserOptionError, match="Option `count` is missing argument!"):
        parse(Config, ["--amount", "1.0", "--count"], caught=False)
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        parse(Config, ["--count", "2", "--count", "3"], caught=False)


def test_dataclass_with_help_attr():
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
        parse(Config, [], caught=False)


def test_dataclass_with_unsupported_attr_type():
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
        parse(Config, [], caught=False)
