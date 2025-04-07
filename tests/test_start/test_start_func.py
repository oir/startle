from typing import Callable

from pytest import mark, raises

from startle.error import ParserConfigError, ParserOptionError

from ._utils import check, check_exits, run_w_explicit_args, run_w_sys_argv


def hi1(name: str, count: int = 1) -> None:
    for _ in range(count):
        print(f"Hello, {name}!")


def hi2(name: str, count: int = 1, /) -> None:
    for _ in range(count):
        print(f"Hello, {name}!")


def hi3(name: str, /, count: int = 1) -> None:
    for _ in range(count):
        print(f"Hello, {name}!")


def hi4(name: str, /, *, count: int = 1) -> None:
    for _ in range(count):
        print(f"Hello, {name}!")


def hi5(name: str, *, count: int = 1) -> None:
    for _ in range(count):
        print(f"Hello, {name}!")


def hi6(*, name: str, count: int = 1) -> None:
    for _ in range(count):
        print(f"Hello, {name}!")


@mark.parametrize("hi", [hi1, hi2, hi3, hi4, hi5, hi6])
@mark.parametrize("run", [run_w_explicit_args, run_w_sys_argv])
def test_hi(capsys, run: Callable, hi: Callable) -> None:
    if hi in [hi1, hi2, hi3, hi4]:
        check(capsys, run, hi, ["Alice"], "Hello, Alice!\n")

    if hi in [hi1, hi2, hi3]:
        check(capsys, run, hi, ["Bob", "3"], "Hello, Bob!\nHello, Bob!\nHello, Bob!\n")

    if hi in [hi1, hi5, hi6]:
        check(
            capsys,
            run,
            hi,
            ["--name", "Bob", "--count", "3"],
            "Hello, Bob!\nHello, Bob!\nHello, Bob!\n",
        )
        check(
            capsys,
            run,
            hi,
            ["--count", "3", "--name", "Bob"],
            "Hello, Bob!\nHello, Bob!\nHello, Bob!\n",
        )
        check(capsys, run, hi, ["--name", "Alice"], "Hello, Alice!\n")

    if hi in [hi1, hi3, hi4, hi5]:
        check(
            capsys,
            run,
            hi,
            ["--count", "3", "Bob"],
            "Hello, Bob!\nHello, Bob!\nHello, Bob!\n",
        )
        check(
            capsys,
            run,
            hi,
            ["Bob", "--count", "3"],
            "Hello, Bob!\nHello, Bob!\nHello, Bob!\n",
        )

    if hi is hi1:
        check(
            capsys,
            run,
            hi,
            ["--name", "Bob", "3"],
            "Hello, Bob!\nHello, Bob!\nHello, Bob!\n",
        )


@mark.parametrize("hi", [hi1, hi2, hi3, hi4, hi5, hi6])
@mark.parametrize("run", [run_w_explicit_args, run_w_sys_argv])
def test_parse_err(capsys, run: Callable, hi: Callable) -> None:
    if hi in [hi1, hi5, hi6]:
        check_exits(
            capsys, run, hi, [], "Error: Required option `name` is not provided!"
        )
        check_exits(
            capsys,
            run,
            hi,
            ["--name", "Bob", "--count", "3", "--name", "Alice"],
            "Error: Option `name` is multiply given!",
        )
        check_exits(
            capsys,
            run,
            hi,
            ["--name", "Bob", "--count", "3", "--lastname", "Alice"],
            "Error: Unexpected option `lastname`!",
        )
        with raises(ParserOptionError, match="Required option `name` is not provided!"):
            run(hi, [], caught=False)
        with raises(ParserOptionError, match="Option `name` is multiply given!"):
            run(hi, ["--name", "Bob", "--count", "3", "--name", "Alice"], caught=False)
        with raises(ParserOptionError, match="Unexpected option `lastname`!"):
            run(
                hi,
                ["--name", "Bob", "--count", "3", "--lastname", "Alice"],
                caught=False,
            )
    else:
        check_exits(
            capsys,
            run,
            hi,
            [],
            "Error: Required positional argument <name> is not provided!",
        )
        with raises(
            ParserOptionError,
            match="Required positional argument <name> is not provided!",
        ):
            run(hi, [], caught=False)


@mark.parametrize("run", [run_w_explicit_args, run_w_sys_argv])
def test_config_err(capsys, run: Callable) -> None:
    def f(help: bool = False) -> None:
        pass

    check_exits(
        capsys, run, f, [], "Error: Cannot use `help` as parameter name in `f()`!"
    )
    with raises(
        ParserConfigError, match=r"Cannot use `help` as parameter name in `f\(\)`!"
    ):
        run(f, [], caught=False)
