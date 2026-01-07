from collections.abc import Callable

from pytest import mark

from ._utils import Opt, Opts, check_args


def hi1(msg: str | None = None) -> None:
    print(f"{msg or 'hi'}!")


def hi2(msg: None | str = None) -> None:
    print(f"{msg or 'hi'}!")


def hi3(msg: str | None = None) -> None:
    print(f"{msg or 'hi'}!")


def hi4(msg: str | None = None) -> None:
    print(f"{msg or 'hi'}!")


@mark.parametrize("hi", [hi1, hi2, hi3, hi4])
@mark.parametrize("opt", Opts())
def test_optional_str(hi: Callable, opt: Opt):
    check_args(hi, [], [None], {})
    check_args(hi, opt("msg", ["hello"]), ["hello"], {})


def int_digits1(number: int | None = None) -> None:
    print(f"{number or 0}!")


def int_digits2(number: None | int = None) -> None:
    print(f"{number or 0}!")


def int_digits3(number: int | None = None) -> None:
    print(f"{number or 0}!")


def int_digits4(number: int | None = None) -> None:
    print(f"{number or 0}!")


@mark.parametrize("int_digits", [int_digits1, int_digits2, int_digits3, int_digits4])
@mark.parametrize("opt", Opts())
def test_optional_int(int_digits: Callable, opt: Opt):
    check_args(int_digits, [], [None], {})
    check_args(int_digits, opt("number", ["3"]), [3], {})


def float_digits1(number: float | None = None) -> None:
    print(f"{number or 0.0}!")


def float_digits2(number: None | float = None) -> None:
    print(f"{number or 0.0}!")


def float_digits3(number: float | None = None) -> None:
    print(f"{number or 0.0}!")


def float_digits4(number: float | None = None) -> None:
    print(f"{number or 0.0}!")


@mark.parametrize(
    "float_digits", [float_digits1, float_digits2, float_digits3, float_digits4]
)
@mark.parametrize("opt", Opts())
def test_optional_float(float_digits: Callable, opt: Opt):
    check_args(float_digits, [], [None], {})
    check_args(float_digits, opt("number", ["3.14"]), [3.14], {})


def maybe1(predicate: bool | None = None) -> None:
    print(f"{predicate or False}!")


def maybe2(predicate: None | bool = None) -> None:
    print(f"{predicate or False}!")


def maybe3(predicate: bool | None = None) -> None:
    print(f"{predicate or False}!")


def maybe4(predicate: bool | None = None) -> None:
    print(f"{predicate or False}!")


@mark.parametrize("maybe", [maybe1, maybe2, maybe3, maybe4])
@mark.parametrize(
    "true", ["true", "True", "TRUE", "t", "T", "yes", "Yes", "YES", "y", "Y", "1"]
)
@mark.parametrize(
    "false", ["false", "False", "FALSE", "f", "F", "no", "No", "NO", "n", "N", "0"]
)
@mark.parametrize("opt", Opts())
def test_optional_bool(maybe: Callable, true: str, false: str, opt: Opt):
    check_args(maybe, [], [None], {})
    check_args(maybe, opt("predicate", [true]), [True], {})
    check_args(maybe, opt("predicate", [false]), [False], {})
