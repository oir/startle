import re
import sys
from typing import Any, List, Literal, Optional, Union

from pytest import mark, raises
from startle._inspect.classes import get_default_factories
from startle._typing import (
    normalize,
    shorten,
    strip_not_required,
    strip_optional,
    strip_required,
)
from startle.arg import Arg, Name
from startle.args import Args
from startle.error import ParserConfigError


def test_normalize():
    assert normalize(int) is int
    assert normalize(Union[int, None]) == Optional[int]
    assert normalize(int | None) == Optional[int]
    assert normalize(Optional[int]) == Optional[int]

    assert normalize(Union[str, float]) == Union[str, float]
    assert normalize(str | float) == Union[str, float]


def test_strip_optional():
    def normalize_strip_optional(type_: Any) -> Any:
        return strip_optional(normalize(type_))

    assert normalize_strip_optional(int) is int
    assert normalize_strip_optional(Union[int, None]) is int
    assert normalize_strip_optional(int | None) is int
    assert normalize_strip_optional(Optional[int]) is int

    assert normalize_strip_optional(Union[str, float, None]) == Union[str, float]
    assert normalize_strip_optional(str | float | None) == Union[str, float]
    assert normalize_strip_optional(Optional[str | float]) == Union[str, float]

    assert normalize_strip_optional(Union[str, float]) == Union[str, float]
    assert normalize_strip_optional(str | float) == Union[str, float]


def test_shorten():
    assert shorten(int) == "int"
    assert shorten(str) == "str"
    assert shorten(float) == "float"
    assert shorten(bool) == "bool"

    assert shorten(Union[int, str]) == "int | str"
    assert shorten(str | float) == "str | float"
    assert shorten(Union[str, float]) == "str | float"
    assert shorten(Union[int, None]) == "int | None"
    assert shorten(Optional[int]) == "int | None"

    assert shorten(str | float | None) == "str | float | None"
    assert shorten(str | None | float) == "str | float | None"
    assert shorten(None | str | float) == "str | float | None"
    assert shorten(Union[str, float, None]) == "str | float | None"
    assert shorten(Union[str, None, float]) == "str | float | None"
    assert shorten(Optional[str | float]) == "str | float | None"

    assert shorten(list[int]) == "list[int]"
    assert shorten(List[int]) == "list[int]"
    assert shorten(List[int | None]) == "list[int | None]"
    assert shorten(list[int | None] | None) == "list[int | None] | None"
    assert shorten(list) == "list"  # type: ignore
    assert shorten(List) == "typing.List"  # TODO:
    assert shorten(Any) in ["Any", "typing.Any"]  # TODO:
    assert shorten(list[list]) == "list[list]"  # type: ignore

    assert shorten(Literal[1]) == "Literal[1]"
    assert shorten(Literal["a"]) == "Literal['a']"


def test_arg_properties():
    a = Arg(name=Name(long="blip"), type_=int, is_positional=False, is_named=True)
    assert not a.is_flag
    assert not a.is_nary

    a = Arg(
        name=Name(long="blip"),
        type_=bool,
        is_positional=False,
        is_named=True,
        default=False,
    )
    assert a.is_flag
    assert not a.is_nary

    a = Arg(
        name=Name(long="blip"),
        type_=bool,
        is_positional=False,
        is_named=True,
        required=True,
    )
    assert not a.is_flag
    assert not a.is_nary

    a = Arg(
        name=Name(long="blip"),
        type_=int,
        is_positional=False,
        is_named=True,
        is_nary=True,
        container_type=list,
    )
    assert not a.is_flag
    assert a.is_nary

    a = Arg(
        name=Name(long="blip"),
        type_=int,
        is_positional=True,
        is_named=False,
        is_nary=True,
        container_type=tuple,
    )
    assert not a.is_flag
    assert a.is_nary

    with raises(
        ParserConfigError,
        match=re.escape("An argument should be either positional or named (or both)!"),
    ):
        a = Arg(name=Name(long="blip"), type_=int)

    with raises(ParserConfigError, match=re.escape("Unsupported container type!")):
        a = Arg(
            name=Name(long="blip"),
            type_=int,
            is_positional=True,
            is_named=False,
            is_nary=True,
            container_type=dict,
        )
        a.parse("5")

    a = Arg(name=Name(long=""), type_=int, is_positional=False, is_named=True)
    args = Args()
    with raises(
        ParserConfigError,
        match=re.escape("Named arguments should have at least one name!"),
    ):
        args.add(a)

    a = Arg(name=Name(long="name"), type_=int, is_named=True, is_nary=True)
    with raises(
        ParserConfigError,
        match=re.escape("Container type must be specified for n-ary options!"),
    ):
        args.enable_unknown_args(a)
    with raises(
        ParserConfigError,
        match=re.escape("Container type must be specified for n-ary options!"),
    ):
        args.enable_unknown_opts(a)


def test_get_default_factories():
    from dataclasses import dataclass, field

    @dataclass
    class Example:
        a: int = 5
        b: List[int] = field(default_factory=lambda: [1, 2, 3])
        c: Optional[str] = None

    factories = get_default_factories(Example)
    assert "a" not in factories
    assert "c" not in factories
    assert callable(factories["b"])
    assert factories["b"]() == [1, 2, 3]

    class NotADataclass:
        pass

    with raises(ValueError, match=re.escape(f"{NotADataclass} is not a dataclass")):
        get_default_factories(NotADataclass)


@mark.skipif(
    sys.version_info < (3, 11),
    reason="Requires Python 3.11+ for NotRequired and Required",
)
def test_strip_not_required_and_required():
    from typing import NotRequired, Required, TypedDict

    class ExampleDict(TypedDict):
        a: NotRequired[int]
        b: Required[str]
        c: float

    is_not_required, type_a = strip_not_required(ExampleDict.__annotations__["a"])
    assert is_not_required is True
    assert type_a is int

    is_required, type_b = strip_required(ExampleDict.__annotations__["b"])
    assert is_required is True
    assert type_b is str

    is_required, type_c = strip_required(ExampleDict.__annotations__["c"])
    assert is_required is False
    assert type_c is float
