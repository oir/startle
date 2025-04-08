from typing import Optional, Union

from startle._type_utils import (
    _normalize_type,
    _shorten_type_annotation,
    _strip_optional,
)


def test_normalize_type():
    assert _normalize_type(int) is int
    assert _normalize_type(Union[int, None]) is Optional[int]
    assert _normalize_type(int | None) is Optional[int]
    assert _normalize_type(Optional[int]) is Optional[int]

    assert _normalize_type(Union[str, float]) is Union[str, float]
    assert _normalize_type(str | float) is Union[str, float]


def test_strip_optional():
    def normalize_strip_optional(type_: type) -> type:
        return _strip_optional(_normalize_type(type_))

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
    assert _shorten_type_annotation(int) == "int"
    assert _shorten_type_annotation(str) == "str"
    assert _shorten_type_annotation(float) == "float"
    assert _shorten_type_annotation(bool) == "bool"

    assert _shorten_type_annotation(Union[int, str]) == "int | str"
    assert _shorten_type_annotation(str | float) == "str | float"
    assert _shorten_type_annotation(Union[str, float]) == "str | float"
    assert _shorten_type_annotation(Union[int, None]) == "int | None"
    assert _shorten_type_annotation(Optional[int]) == "int | None"
