from typing import Callable

from pytest import mark

from ._utils import check, check_exits, run_w_explicit_args, run_w_sys_argv


def add(a: int, b: int) -> None:
    """
    Add two numbers.

    Args:
        a: The first number.
        b: The second number.
    """
    print(f"{a} + {b} = {a + b}")


def sub(a: int, b: int) -> None:
    """
    Subtract two numbers.

    Args:
        a: The first number.
        b: The second number
    """
    print(f"{a} - {b} = {a - b}")


def mul(a: int, b: int) -> None:
    """
    Multiply two numbers.

    Args:
        a: The first number.
        b: The second number.
    """
    print(f"{a} * {b} = {a * b}")


def div(a: int, b: int) -> None:
    """
    Divide two numbers.

    Args:
        a: The dividend.
        b: The divisor.
    """
    print(f"{a} / {b} = {a / b}")


@mark.parametrize("run", [run_w_explicit_args, run_w_sys_argv])
def test_calc(capsys, run: Callable) -> None:
    check(capsys, run, [add, sub, mul, div], ["add", "2", "3"], "2 + 3 = 5\n")
    check(capsys, run, [add, sub, mul, div], ["sub", "2", "3"], "2 - 3 = -1\n")
    check(capsys, run, [add, sub, mul, div], ["mul", "2", "3"], "2 * 3 = 6\n")
    check(capsys, run, [add, sub, mul, div], ["div", "6", "3"], "6 / 3 = 2.0\n")

    check_exits(
        capsys, run, [add, sub, mul, div], ["2", "3"], "Error: Unknown command `2`!\n"
    )
    check_exits(capsys, run, [add, sub, mul, div], [], "Error: No command given!\n")

    check_exits(
        capsys,
        run,
        [add, sub, mul, div],
        ["add", "2", "3", "4"],
        "Error: Unexpected positional argument: `4`!\n",
    )
    check_exits(
        capsys,
        run,
        [add, sub, mul, div],
        ["sub", "2"],
        "Error: Required option `b` is not provided!\n",
    )
