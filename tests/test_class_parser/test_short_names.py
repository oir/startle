from dataclasses import dataclass

from startle.inspect import make_args_from_class


@dataclass
class Cls1:
    name: str = "john"
    count: int = 1


@dataclass
class Cls2:
    name: str = "john"
    count: int = 1
    c: int = 2


@dataclass
class Cls3:
    """
    A class.

    Attributes:
        name: The name of the person.
        count: The number of times to greet.
        c: The number of times to groot.
    """

    name: str = "john"
    count: int = 1
    c: int = 2


@dataclass
class Cls4:
    """
    A class.

    Attributes:
        name: The name of the person.
        count [k]: The number of times to greet.
        c: The number of times to groot.
    """

    name: str = "john"
    count: int = 1
    c: int = 2


@dataclass
class Cls5:
    """
    A class.

    Attributes:
        cake: The type of cake.
        count: The number of cakes.
        c: The number of times to groot.
        frosting [c]: The amount of frosting.
    """

    cake: str = "john"
    count: int = 1
    c: int = 2
    frosting: int = 3


@dataclass
class Cls6:
    """
    A class.

    Attributes:
        cake: The type of cake.
        count: The number of cakes.
        frosting [c]: The amount of frosting.
    """

    cake: str = "john"
    count: int = 1
    frosting: int = 3


def test_short_names():
    args = make_args_from_class(Cls1)
    assert args._name2idx["c"] == args._name2idx["count"]

    args = make_args_from_class(Cls2)
    assert args._name2idx["c"] != args._name2idx["count"]

    args = make_args_from_class(Cls3)
    assert args._name2idx["c"] != args._name2idx["count"]

    args = make_args_from_class(Cls4)
    assert args._name2idx["k"] == args._name2idx["count"]
    assert args._name2idx["c"] != args._name2idx["count"]

    args = make_args_from_class(Cls5)
    assert args._name2idx["c"] != args._name2idx["cake"]
    assert args._name2idx["c"] != args._name2idx["count"]
    assert args._name2idx["c"] != args._name2idx["frosting"]

    args = make_args_from_class(Cls6)
    assert args._name2idx["c"] != args._name2idx["cake"]
    assert args._name2idx["c"] == args._name2idx["frosting"]
    assert args._name2idx["c"] != args._name2idx["count"]
