#!/usr/bin/env python3.12

"""
This file needs to be skipped entirely in Python < 3.12 because it uses
the new `type` syntax for type aliases, it is a syntax error in older versions,
that cannot be gracefully handled with `if sys.version_info < (3, 12): ...`.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from pytest import mark, raises
from startle import parse, register
from startle._metavar import METAVARS
from startle._value_parser import PARSERS
from startle.error import ParserConfigError, ParserOptionError, ParserValueError

from ._utils import check_args
from .test_parse_class import check_parse_exits

type MyFloat = float
type MyStr = str
type MyFloat2 = MyFloat
type MyFloat3 = Annotated[MyFloat, "some metadata"]


def hi_float_annotated(
    name: Annotated[str, "some metadata"] = "john",
    /,
    *,
    count: Annotated[float, "some metadata"] = 1.0,
) -> None:
    for _ in range(int(count)):
        print(f"hello, {name}!")


def hi_type_alias(name: MyStr = "john", /, *, count: MyFloat = 1.0) -> None:
    for _ in range(int(count)):
        print(f"hello, {name}!")


def hi_type_alias_nested(name: MyStr = "john", /, *, count: MyFloat2 = 1.0) -> None:
    for _ in range(int(count)):
        print(f"hello, {name}!")


def hi_type_alias_nested_annotated(
    name: MyStr = "john", /, *, count: MyFloat3 = 1.0
) -> None:
    for _ in range(int(count)):
        print(f"hello, {name}!")


@mark.parametrize(
    "hi, count_t",
    [
        (hi_float_annotated, float),
        (hi_type_alias, float),
        (hi_type_alias_nested, float),
        (hi_type_alias_nested_annotated, float),
    ],
)
def test_args_with_defaults(hi, count_t):
    typestr = "integer" if count_t is int else "float"

    check_args(hi, [], ["john"], {"count": count_t(1)})
    check_args(hi, ["jane"], ["jane"], {"count": count_t(1)})
    check_args(hi, ["jane", "--count", "3"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["jane", "--count=3"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["--count", "3", "jane"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["--count", "3", "--", "jane"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["--count", "3"], ["john"], {"count": count_t(3)})
    check_args(hi, ["--count", "3", "--"], ["john"], {"count": count_t(3)})
    check_args(hi, ["jane", "-c", "3"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["jane", "-c=3"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["-c", "3", "jane"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["-c", "3", "--", "jane"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["-c", "3"], ["john"], {"count": count_t(3)})

    with raises(ParserValueError, match=f"Cannot parse {typestr} from `x`!"):
        check_args(hi, ["jane", "--count", "x"], [], {})
    with raises(ParserValueError, match=f"Cannot parse {typestr} from `x`!"):
        check_args(hi, ["--count", "x", "jane"], [], {})
    with raises(ParserValueError, match=f"Cannot parse {typestr} from `x`!"):
        check_args(hi, ["--count", "x", "--", "jane"], [], {})
    with raises(ParserValueError, match=f"Cannot parse {typestr} from `x`!"):
        check_args(hi, ["jane", "--count=x"], [], {})

    with raises(ParserOptionError, match="Unexpected positional argument: `3`!"):
        check_args(hi, ["john", "3"], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `3`!"):
        check_args(hi, ["john", "--", "3"], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `3`!"):
        check_args(hi, ["--", "john", "3"], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `--`!"):
        # Second `--` will be treated as a positional argument as is
        check_args(hi, ["--", "john", "--", "3"], [], {})

    with raises(ParserOptionError, match="Option `count` is missing argument!"):
        check_args(hi, ["--count"], [], {})
    with raises(ParserOptionError, match="Option `count` is missing argument!"):
        check_args(hi, ["jane", "--count"], [], {})

    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["--name", "jane"], [], {})
    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["--name", "jane", "john"], [], {})
    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["john", "--name", "jane"], [], {})
    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["--name=jane"], [], {})

    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["john", "--count", "3", "--count", "4"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["john", "--count", "3", "-c", "4"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["john", "--count=3", "--count", "4"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["john", "--count", "3", "--count=4"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["--count", "3", "john", "--count", "4"], [], {})

    # with raises(ParserOptionError, match="Prefix `--` is not followed by an option!"):
    #    check_args(hi, ["john", "-c", "3", "--"], [], {})
    with raises(ParserOptionError, match="Prefix `-` is not followed by an option!"):
        check_args(hi, ["john", "-"], [], {})


@dataclass
class ConfigDataClass:
    """
    A configuration class for the program.
    """

    count: int = 1
    amount: MyFloat3 = 1.0
    label: MyStr = "default"


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
        lambda label: ["--label", f"{label}"],
        lambda label: [f"--label={label}"],
        lambda label: ["-l", f"{label}"],
        lambda label: [f"-l={label}"],
    ],
)
@mark.parametrize("Config", [ConfigDataClass])
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


@dataclass
class Rational:
    num: int
    den: int

    def __repr__(self):
        return f"{self.num}/{self.den}"


type MyRational = Rational


def mul(a: Rational, b: Rational) -> Rational:
    """
    Multiply two rational numbers.
    """
    y = Rational(a.num * b.num, a.den * b.den)
    print(f"{a} * {b} = {y}")
    return y


def mul2(a: MyRational, b: Rational) -> Rational:
    """
    Multiply two rational numbers.
    """
    y = Rational(a.num * b.num, a.den * b.den)
    print(f"{a} * {b} = {y}")
    return y


def mul3(a: MyRational, b: MyRational) -> MyRational:
    """
    Multiply two rational numbers.
    """
    y = Rational(a.num * b.num, a.den * b.den)
    print(f"{a} * {b} = {y}")
    return y


@mark.parametrize("mul_f", [mul, mul2, mul3])
@mark.parametrize("register_t", [Rational, MyRational])
def test_unsupported_type(mul_f, register_t):
    a_type = "Rational" if mul_f is mul else "MyRational"
    with raises(
        ParserConfigError,
        match=re.escape(
            f"Unsupported type `{a_type}` for parameter `a` in `{mul_f.__name__}()`!"
        ),
    ):
        check_args(mul_f, ["1/2", "3/4"], [], {})

    register(
        register_t,
        parser=lambda value: Rational(*map(int, value.split("/"))),
        metavar="<int>/<int>",
    )

    check_args(mul_f, ["1/2", "3/4"], [Rational(1, 2), Rational(3, 4)], {})
    check_args(mul_f, ["-a", "1/2", "3/4"], [Rational(1, 2), Rational(3, 4)], {})
    check_args(mul_f, ["-a", "1/2", "-b", "3/4"], [Rational(1, 2), Rational(3, 4)], {})
    check_args(mul_f, ["1/2", "-b", "3/4"], [Rational(1, 2), Rational(3, 4)], {})
    check_args(mul_f, ["-b", "3/4", "1/2"], [Rational(1, 2), Rational(3, 4)], {})
    check_args(mul_f, ["-b", "3/4", "--", "1/2"], [Rational(1, 2), Rational(3, 4)], {})

    del PARSERS[Rational]
    del METAVARS[Rational]
