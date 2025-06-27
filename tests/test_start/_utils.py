import sys
from typing import Callable

from pytest import raises

from startle import start


def run_w_explicit_args(
    func: Callable | list[Callable] | dict[str, Callable],
    args: list[str],
    name: str | None = None,
    catch: bool = True,
    default: str | None = None,
) -> None:
    start(func, name=name, args=args, catch=catch, default=default)


def run_w_sys_argv(
    func: Callable | list[Callable] | dict[str, Callable],
    args: list[str],
    name: str | None = None,
    catch: bool = True,
    default: str | None = None,
) -> None:
    old_argv = sys.argv[1:]
    sys.argv[1:] = args
    start(func, name=name, catch=catch, default=default)
    sys.argv[1:] = old_argv


def check(
    capsys,
    run: Callable,
    f: Callable | list[Callable] | dict[str, Callable],
    args: list[str],
    expected: str,
) -> None:
    run(f, args)
    captured = capsys.readouterr()
    assert captured.out == expected


def check_exits(
    capsys,
    run: Callable,
    f: Callable,
    args: list[str],
    expected: str,
    *,
    exit_code: str = "1",
) -> None:
    with raises(SystemExit) as excinfo:
        run(f, args)
    assert str(excinfo.value) == exit_code
    captured = capsys.readouterr()
    assert captured.out.startswith(expected)
