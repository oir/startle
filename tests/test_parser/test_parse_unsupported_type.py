from typing import Callable

from _utils import check_args
from pytest import mark, raises

from startle._type_utils import _normalize_type
from startle.error import ParserConfigError


class Spell:
    pass


def cast_one(spell: Spell):
    print(f"Casting {spell}.")


def cast_maybe(spell: Spell | None = None):
    print(f"Casting {spell}.")


def cast_many(spells: list[Spell]):
    print(f"Casting {spells}.")


@mark.parametrize(
    "cast,name,type_",
    [
        (cast_one, "spell", Spell),
        (cast_maybe, "spell", Spell | None),
        (cast_many, "spells", Spell),  # for nargs, the type is the element type
    ],
)
def test_unsupported_type(cast: Callable, name: str, type_: type):
    with raises(
        ParserConfigError,
        match=f"Unsupported type: {_normalize_type(type_).__name__} for parameter {name} in {cast.__name__}!",
    ):
        check_args(cast, [], [], {})
