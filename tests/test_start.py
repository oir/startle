from startle import start
from typing import Callable
import sys

from pytest import mark

def hi(name: str, count: int = 1) -> None:
    for _ in range(count):
        print(f"Hello, {name}!")

def run1(func: Callable[..., None], args: list[str]) -> None:
    start(func, args)

def run2(func: Callable[..., None], args: list[str]) -> None:
    old_argv = sys.argv[1:]
    sys.argv[1:] = args
    start(func)
    sys.argv[1:] = old_argv

def check(capsys, run: Callable, args: list[str], expected: str) -> None:
    run(hi, args)
    captured = capsys.readouterr()
    assert captured.out == expected


@mark.parametrize("run", [run1, run2])
def test_hi(capsys, run: Callable):
    check(capsys, run, ["Alice"], "Hello, Alice!\n")
    check(capsys, run, ["--name", "Alice"], "Hello, Alice!\n")

    check(capsys, run, ["Bob", "3"], "Hello, Bob!\nHello, Bob!\nHello, Bob!\n")

    check(capsys, run, ["--name", "Bob", "--count", "3"], "Hello, Bob!\nHello, Bob!\nHello, Bob!\n")
    check(capsys, run, ["--count", "3", "--name", "Bob"], "Hello, Bob!\nHello, Bob!\nHello, Bob!\n")

    check(capsys, run, ["--count", "3", "Bob"], "Hello, Bob!\nHello, Bob!\nHello, Bob!\n")
    check(capsys, run, ["Bob", "--count", "3"], "Hello, Bob!\nHello, Bob!\nHello, Bob!\n")

    check(capsys, run, ["--name", "Bob", "3"], "Hello, Bob!\nHello, Bob!\nHello, Bob!\n")
