import sys
from typing import Callable

from pytest import mark, raises

from startle import start


def run1(func: Callable[..., None], args: list[str]) -> None:
    start(func, args)


def run2(func: Callable[..., None], args: list[str]) -> None:
    old_argv = sys.argv[1:]
    sys.argv[1:] = args
    start(func)
    sys.argv[1:] = old_argv


def check(capsys, run: Callable, f: Callable, args: list[str], expected: str) -> None:
    run(f, args)
    captured = capsys.readouterr()
    assert captured.out == expected


def check_exits(
    capsys, run: Callable, f: Callable, args: list[str], expected: str
) -> None:
    with raises(SystemExit) as excinfo:
        run(f, args)
    assert str(excinfo.value) == "1"
    captured = capsys.readouterr()
    assert captured.out.startswith(expected)


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
@mark.parametrize("run", [run1, run2])
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
@mark.parametrize("run", [run1, run2])
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
    else:
        check_exits(
            capsys,
            run,
            hi,
            [],
            "Error: Required positional argument <name> is not provided!",
        )


@mark.parametrize("run", [run1, run2])
def test_config_err(capsys, run: Callable) -> None:
    def f(help: bool = False) -> None:
        pass

    check_exits(
        capsys, run, f, [], "Error: Cannot use `help` as parameter name in f()!"
    )
