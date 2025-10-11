#!/usr/bin/env python3.12

"""
This file needs to be skipped entirely in Python < 3.12 because it uses
the new `type` syntax for type aliases, it is a syntax error in older versions,
that cannot be gracefully handled with `if sys.version_info < (3, 12): ...`.
"""

from typing import Annotated

from pytest import mark, raises

from startle.error import ParserOptionError, ParserValueError

from ._utils import check_args

type MyFloat2 = float


def hi_int(name: str = "john", /, *, count: int = 1) -> None:
    for _ in range(count):
        print(f"hello, {name}!")


def hi_float(name: str = "john", /, *, count: float = 1.0) -> None:
    for _ in range(int(count)):
        print(f"hello, {name}!")


def hi_float_annotated(
    name: Annotated[str, "some metadata"] = "john",
    /,
    *,
    count: Annotated[float, "some metadata"] = 1.0,
) -> None:
    for _ in range(int(count)):
        print(f"hello, {name}!")


@mark.parametrize(
    "hi, count_t", [(hi_int, int), (hi_float, float), (hi_float_annotated, float)]
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
