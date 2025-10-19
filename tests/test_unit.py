import re
from typing import Any, Optional, Union

from pytest import raises

from startle._type_utils import (
    normalize_type,
    shorten_type_annotation,
    strip_optional,
)
from startle.arg import Arg, Name
from startle.error import ParserConfigError


def test_normalize_type():
    assert normalize_type(int) is int
    assert normalize_type(Union[int, None]) is Optional[int]
    assert normalize_type(int | None) is Optional[int]
    assert normalize_type(Optional[int]) is Optional[int]

    assert normalize_type(Union[str, float]) is Union[str, float]
    assert normalize_type(str | float) is Union[str, float]


def test_strip_optional():
    def normalize_strip_optional(type_: Any) -> Any:
        return strip_optional(normalize_type(type_))

    assert normalize_strip_optional(int) is int
    assert normalize_strip_optional(Union[int, None]) is int
    assert normalize_strip_optional(int | None) is int
    assert normalize_strip_optional(Optional[int]) is int

    assert normalize_strip_optional(Union[str, float, None]) is Union[str, float]
    assert normalize_strip_optional(str | float | None) is Union[str, float]
    assert normalize_strip_optional(Optional[str | float]) is Union[str, float]

    assert normalize_strip_optional(Union[str, float]) is Union[str, float]
    assert normalize_strip_optional(str | float) is Union[str, float]


def test_shorten_type_annotation():
    from typing import Any, List, Literal

    assert shorten_type_annotation(int) == "int"
    assert shorten_type_annotation(str) == "str"
    assert shorten_type_annotation(float) == "float"
    assert shorten_type_annotation(bool) == "bool"

    assert shorten_type_annotation(Union[int, str]) == "int | str"
    assert shorten_type_annotation(str | float) == "str | float"
    assert shorten_type_annotation(Union[str, float]) == "str | float"
    assert shorten_type_annotation(Union[int, None]) == "int | None"
    assert shorten_type_annotation(Optional[int]) == "int | None"

    assert shorten_type_annotation(str | float | None) == "str | float | None"
    assert shorten_type_annotation(str | None | float) == "str | float | None"
    assert shorten_type_annotation(None | str | float) == "str | float | None"
    assert shorten_type_annotation(Union[str, float, None]) == "str | float | None"
    assert shorten_type_annotation(Union[str, None, float]) == "str | float | None"
    assert shorten_type_annotation(Optional[str | float]) == "str | float | None"

    assert shorten_type_annotation(list[int]) == "list[int]"
    assert shorten_type_annotation(List[int]) == "list[int]"
    assert shorten_type_annotation(List[int | None]) == "list[int | None]"
    assert (
        shorten_type_annotation(list[int | None] | None) == "list[int | None] | None"
    )
    assert shorten_type_annotation(list) == "list"
    assert shorten_type_annotation(List) == "typing.List"  # TODO:
    assert shorten_type_annotation(Any) in ["Any", "typing.Any"]  # TODO:
    assert shorten_type_annotation(list[list]) == "list[list]"

    assert shorten_type_annotation(Literal[1]) == "Literal[1]"
    assert shorten_type_annotation(Literal["a"]) == "Literal['a']"


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
