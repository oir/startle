from typing import Callable

from pytest import mark, raises

from startle.error import ParserOptionError

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
    check(
        capsys,
        run,
        {"sum": add, "sub": sub, "mul": mul, "div": div},
        ["sum", "2", "3"],
        "2 + 3 = 5\n",
    )

    check_exits(
        capsys, run, [add, sub, mul, div], ["--help"], "\nUsage:\n", exit_code="0"
    )
    check_exits(
        capsys,
        run,
        [add, sub, mul, div],
        ["add", "--help"],
        "\nAdd two numbers.\n\nUsage:\n",
        exit_code="0",
    )

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

    with raises(ParserOptionError, match=r"Unknown command `2`!"):
        run([add, sub, mul, div], ["2", "3"], caught=False)
    with raises(ParserOptionError, match=r"No command given!"):
        run([add, sub, mul, div], [], caught=False)
    with raises(ParserOptionError, match=r"Unexpected positional argument: `4`!"):
        run([add, sub, mul, div], ["add", "2", "3", "4"], caught=False)
    with raises(ParserOptionError, match=r"Required option `b` is not provided!"):
        run([add, sub, mul, div], ["sub", "2"], caught=False)
