import re
from typing import Callable

from _utils import check_args
from pytest import mark, raises

from startle.error import ParserConfigError


class Spell:
    pass


def cast_one(spell: Spell):
    print(f"Casting {spell}.")


def cast_maybe(spell: Spell | None = None):
    print(f"Casting {spell}.")


def cast_many(spells: list[Spell]):
    print(f"Casting {spells}.")


# nested lists are not supported
def read_too_many_spellbooks(spellbook: list[list[str]]):
    print(f"Reading {spellbook}.")


@mark.parametrize(
    "cast,name,type_",
    [
        (cast_one, "spell", Spell),
        (cast_maybe, "spell", Spell | None),
        (cast_many, "spells", list[Spell]),
        (read_too_many_spellbooks, "spellbook", list[list[str]]),
    ],
)
def test_unsupported_type(cast: Callable, name: str, type_: type):
    with raises(
        ParserConfigError,
        match=re.escape(
            f"Unsupported type: {type_} for parameter {name} in {cast.__name__}!"
        ),
    ):
        check_args(cast, [], [], {})
