import sys
from collections.abc import Callable
from typing import Any

from pytest import raises, CaptureFixture
from startle import start


def remove_trailing_spaces(text: str) -> str:
    lines = text.split("\n")
    return "\n".join(line.rstrip() for line in lines)


Funcs = Callable[..., Any] | list[Callable[..., Any]] | dict[str, Callable[..., Any]]


def run_w_explicit_args(
    func: Funcs,
    args: list[str],
    name: str | None = None,
    catch: bool = True,
    default: str | None = None,
) -> None:
    start(func, name=name, args=args, catch=catch, default=default)


def run_w_sys_argv(
    func: Funcs,
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
    capsys: CaptureFixture[str],
    run: Callable[..., Any],
    f: Funcs,
    args: list[str],
    expected: str,
) -> None:
    run(f, args)
    captured = capsys.readouterr()
    assert remove_trailing_spaces(captured.out) == remove_trailing_spaces(expected)


def check_exits(
    capsys: CaptureFixture[str],
    run: Callable[..., Any],
    f: Funcs,
    args: list[str],
    expected: str,
    *,
    exit_code: str = "1",
) -> None:
    with raises(SystemExit) as excinfo:
        run(f, args)
    assert str(excinfo.value) == exit_code
    captured = capsys.readouterr()
    assert remove_trailing_spaces(captured.out).startswith(
        remove_trailing_spaces(expected)
    )
