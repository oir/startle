from typing import Callable, Optional, Union

from _utils import check_args
from pytest import mark


def hi1(msg: str | None = None) -> None:
    print(f"{msg or 'hi'}!")


def hi2(msg: None | str = None) -> None:
    print(f"{msg or 'hi'}!")


def hi3(msg: Optional[str] = None) -> None:
    print(f"{msg or 'hi'}!")


def hi4(msg: Union[str, None] = None) -> None:
    print(f"{msg or 'hi'}!")


@mark.parametrize("hi", [hi1, hi2, hi3, hi4])
def test_optional_str(hi: Callable):
    check_args(hi, [], [], {"msg": None})
    check_args(hi, ["hello"], [], {"msg": "hello"})
    check_args(hi, ["--msg", "hello"], [], {"msg": "hello"})


def int_digits1(number: int | None = None) -> None:
    print(f"{number or 0}!")


def int_digits2(number: None | int = None) -> None:
    print(f"{number or 0}!")


def int_digits3(number: Optional[int] = None) -> None:
    print(f"{number or 0}!")


def int_digits4(number: Union[int, None] = None) -> None:
    print(f"{number or 0}!")


@mark.parametrize("int_digits", [int_digits1, int_digits2, int_digits3, int_digits4])
def test_optional_int(int_digits: Callable):
    check_args(int_digits, [], [], {"number": None})
    check_args(int_digits, ["3"], [], {"number": 3})
    check_args(int_digits, ["--number", "3"], [], {"number": 3})


def float_digits1(number: float | None = None) -> None:
    print(f"{number or 0.0}!")


def float_digits2(number: None | float = None) -> None:
    print(f"{number or 0.0}!")


def float_digits3(number: Optional[float] = None) -> None:
    print(f"{number or 0.0}!")


def float_digits4(number: Union[float, None] = None) -> None:
    print(f"{number or 0.0}!")


@mark.parametrize(
    "float_digits", [float_digits1, float_digits2, float_digits3, float_digits4]
)
def test_optional_float(float_digits: Callable):
    check_args(float_digits, [], [], {"number": None})
    check_args(float_digits, ["3.14"], [], {"number": 3.14})
    check_args(float_digits, ["--number", "3.14"], [], {"number": 3.14})


def maybe1(predicate: bool | None = None) -> None:
    print(f"{predicate or False}!")


def maybe2(predicate: None | bool = None) -> None:
    print(f"{predicate or False}!")


def maybe3(predicate: Optional[bool] = None) -> None:
    print(f"{predicate or False}!")


def maybe4(predicate: Union[bool, None] = None) -> None:
    print(f"{predicate or False}!")


@mark.parametrize("maybe", [maybe1, maybe2, maybe3, maybe4])
@mark.parametrize(
    "true", ["true", "True", "TRUE", "t", "T", "yes", "Yes", "YES", "y", "Y", "1"]
)
@mark.parametrize(
    "false", ["false", "False", "FALSE", "f", "F", "no", "No", "NO", "n", "N", "0"]
)
def test_optional_bool(maybe: Callable, true: str, false: str):
    check_args(maybe, [], [], {"predicate": None})
    check_args(maybe, [true], [], {"predicate": True})
    check_args(maybe, [false], [], {"predicate": False})
    check_args(maybe, ["--predicate", true], [], {"predicate": True})
    check_args(maybe, ["--predicate", false], [], {"predicate": False})
