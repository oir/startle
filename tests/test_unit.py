from typing import Optional, Union

from startle._type_utils import _normalize_type, _strip_optional


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
