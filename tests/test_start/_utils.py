import sys
from typing import Callable

from pytest import raises

from startle import start

def run_w_explicit_args(func: Callable[..., None], args: list[str]) -> None:
    start(func, args)


def run_w_sys_argv(func: Callable[..., None], args: list[str]) -> None:
    old_argv = sys.argv[1:]
    sys.argv[1:] = args
    start(func)
    sys.argv[1:] = old_argv


def check(capsys, run: Callable, f: Callable | list[Callable], args: list[str], expected: str) -> None:
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

