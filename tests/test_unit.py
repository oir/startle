import re
import sys
from typing import (
    Any,
    List,
    Optional,
    Union,
)

from pytest import mark, raises
from startle._inspect.dataclasses import get_default_factories
from startle._type_utils import (
    normalize_annotation,
    shorten_type_annotation,
    strip_not_required,
    strip_optional,
    strip_required,
)
from startle.arg import Arg, Name
from startle.args import Args
from startle.error import ParserConfigError


def test_normalize_annotation():
    assert normalize_annotation(int) is int
    assert normalize_annotation(Union[int, None]) is Optional[int]
    assert normalize_annotation(int | None) is Optional[int]
    assert normalize_annotation(Optional[int]) is Optional[int]

    assert normalize_annotation(Union[str, float]) is Union[str, float]
    assert normalize_annotation(str | float) is Union[str, float]


def test_strip_optional():
    def normalize_strip_optional(type_: Any) -> Any:
        return strip_optional(normalize_annotation(type_))

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
    from typing import Any, Literal

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
    assert shorten_type_annotation(list[int]) == "list[int]"
    assert shorten_type_annotation(list[int | None]) == "list[int | None]"
    assert shorten_type_annotation(list[int | None] | None) == "list[int | None] | None"
    assert shorten_type_annotation(list) == "list"  # type: ignore
    assert shorten_type_annotation(List) == "typing.List"  # TODO:  # noqa
    assert shorten_type_annotation(Any) in ["Any", "typing.Any"]  # TODO:
    assert shorten_type_annotation(list[list]) == "list[list]"  # type: ignore

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
        b: list[int] = field(default_factory=lambda: [1, 2, 3])
        c: str | None = None

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
