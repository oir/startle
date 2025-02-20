from typing import Callable

from pytest import mark, raises

from startle.error import ParserOptionError, ParserValueError

from ._utils import check_args


def hi_w_args(msg: str, n: int, *args) -> None:
    pass


def hi_w_kwargs(msg: str, n: int, **kwargs) -> None:
    pass


def hi_w_nary_kwargs(msg: str, n: int, **kwargs: list[str]) -> None:
    pass


def hi_w_args_kwargs(msg: str, n: int, *args, **kwargs) -> None:
    pass


@mark.parametrize("hi", [hi_w_args, hi_w_args_kwargs])
@mark.parametrize("unks", [[], ["arg1"], ["arg1", "arg2"], ["arg1", "arg2", "arg3"]])
def test_var_args(hi: Callable, unks: list[str]):
    check_args(
        hi,
        ["hello", "3", *unks],
        ["hello", 3, *unks],
        {},
    )


@mark.parametrize("unks", [["arg1", "--arg2"], ["arg1", "arg2", "--arg3=val"]])
def test_var_args_2(unks: list[str]):
    check_args(
        hi_w_args,
        ["hello", "3", *unks],
        ["hello", 3, *unks],
        {},
    )


@mark.parametrize("hi", [hi_w_kwargs, hi_w_args_kwargs])
@mark.parametrize("unks", [{}, {"arg-a": "val1"}, {"arg-a": "val1", "arg-b": "val2"}])
def test_var_kwargs(hi: Callable, unks: dict[str, str]):
    check_args(
        hi,
        ["hello", "3"] + [f"--{k}={v}" for k, v in unks.items()],
        ["hello", 3],
        {k.replace("-", "_"): v for k, v in unks.items()},
    )
    check_args(
        hi,
        ["hello", "3"]
        + [item for kv in unks.items() for item in (f"--{kv[0]}", kv[1])],
        ["hello", 3],
        {k.replace("-", "_"): v for k, v in unks.items()},
    )


@mark.parametrize("hi", [hi_w_nary_kwargs])
@mark.parametrize(
    "cli_args",
    [
        ["hello", "3", "--arg-a=val1", "--arg-a=val2"],
        ["hello", "--arg-a=val1", "--arg-a=val2", "3"],
        ["--arg-a=val1", "--arg-a=val2", "hello", "3"],
        ["--arg-a=val1", "hello", "--arg-a=val2", "3"],
        ["hello", "3", "--arg-a", "val1", "val2"],
        ["hello", "--arg-a", "val1", "val2", "--n", "3"],
        ["--arg-a", "val1", "val2", "--n", "3", "hello"],
    ],
)
def test_var_kwargs_list(hi: Callable, cli_args: list[str]):
    check_args(hi, cli_args, ["hello", 3], {"arg_a": ["val1", "val2"]})


def test_var_kwargs_errors():
    with raises(ParserOptionError, match="Option `arg-a` is missing argument!"):
        check_args(hi_w_kwargs, ["hello", "3", "--arg-a"], [], {})
    with raises(ParserOptionError, match="Required option `msg` is not provided!"):
        check_args(hi_w_nary_kwargs, ["--arg-a", "val1", "val2", "hello", "3"], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `world`!"):
        # because there is kwargs, but not args, the following is invalid
        check_args(
            hi_w_nary_kwargs,
            ["hello", "--arg-a=val1", "--arg-a=val2", "3", "world"],
            [],
            {},
        )

    check_args(
        hi_w_kwargs,
        ["hello", "3", "--arg-a", "--arg-b"],
        ["hello", 3],
        {"arg_a": "--arg-b"},
    )


def test_var_args_kwargs():
    check_args(
        hi_w_args_kwargs,
        ["hello", "3"],
        ["hello", 3],
        {},
    )
    check_args(
        hi_w_args_kwargs,
        ["hello", "3", "arg1", "arg2", "--arg-a=val1", "--arg-b=val2"],
        ["hello", 3, "arg1", "arg2"],
        {"arg_a": "val1", "arg_b": "val2"},
    )
    check_args(
        hi_w_args_kwargs,
        ["hello", "3", "arg1", "arg2", "--arg-a=val1", "--arg-b=val2", "arg3"],
        ["hello", 3, "arg1", "arg2", "arg3"],
        {"arg_a": "val1", "arg_b": "val2"},
    )
    check_args(
        hi_w_args_kwargs,
        ["hello", "3", "arg1", "arg2", "arg3", "--arg-a=val1", "--arg-b", "val2"],
        ["hello", 3, "arg1", "arg2", "arg3"],
        {"arg_a": "val1", "arg_b": "val2"},
    )
    check_args(
        hi_w_args_kwargs,
        ["hello", "3", "arg1", "arg2", "--arg-a=val1", "--arg-b", "val2", "arg3"],
        ["hello", 3, "arg1", "arg2", "arg3"],
        {"arg_a": "val1", "arg_b": "val2"},
    )


def hi_w_args_typed(msg: str, n: int, *args: int) -> None:
    pass


def hi_w_kwargs_typed(msg: str, n: int, **kwargs: float) -> None:
    pass


def hi_w_nary_kwargs_typed(msg: str, n: int, **kwargs: list[float]) -> None:
    pass


def hi_w_args_kwargs_typed(msg: str, n: int, *args: int, **kwargs: float) -> None:
    pass


@mark.parametrize("unks", [[], ["1"], ["1", "2"], ["1", "2", "3"]])
def test_var_args_typed(unks: list[str]):
    check_args(
        hi_w_args_typed,
        ["hello", "3", *unks],
        ["hello", 3, *map(int, unks)],
        {},
    )

    with raises(ParserValueError, match="Cannot parse integer from `arg1`!"):
        check_args(
            hi_w_args_typed,
            ["hello", "3", *unks + ["arg1"]],
            [],
            {},
        )


@mark.parametrize("hi", [hi_w_kwargs_typed, hi_w_args_kwargs_typed])
@mark.parametrize("unks", [{}, {"arg-a": "1.0"}, {"arg-a": "1.0", "arg-b": "2.1"}])
def test_var_kwargs_typed(hi: Callable, unks: dict[str, str]):
    check_args(
        hi,
        ["hello", "3"] + [f"--{k}={v}" for k, v in unks.items()],
        ["hello", 3],
        {k.replace("-", "_"): float(v) for k, v in unks.items()},
    )
    check_args(
        hi,
        ["hello", "3"]
        + [item for kv in unks.items() for item in (f"--{kv[0]}", kv[1])],
        ["hello", 3],
        {k.replace("-", "_"): float(v) for k, v in unks.items()},
    )

    unks_ = unks | {"arg-c": "3.0a"}
    with raises(ParserValueError, match="Cannot parse float from `3.0a`!"):
        check_args(
            hi, ["hello", "3"] + [f"--{k}={v}" for k, v in unks_.items()], [], {}
        )
    with raises(ParserValueError, match="Cannot parse float from `3.0a`!"):
        check_args(
            hi,
            ["hello", "3"]
            + [item for kv in unks_.items() for item in (f"--{kv[0]}", kv[1])],
            [],
            {},
        )


@mark.parametrize("hi", [hi_w_nary_kwargs_typed])
@mark.parametrize(
    "cli_args",
    [
        ["hello", "3", "--arg-a=1.0", "--arg-a=2.1"],
        ["hello", "--arg-a=1.0", "--arg-a=2.1", "3"],
        ["--arg-a=1.0", "--arg-a=2.1", "hello", "3"],
        ["--arg-a=1.0", "hello", "--arg-a=2.1", "3"],
        ["hello", "3", "--arg-a", "1.0", "2.1"],
        ["hello", "--arg-a", "1.0", "2.1", "--n", "3"],
        ["--arg-a", "1.0", "2.1", "--n", "3", "hello"],
    ],
)
def test_var_nary_kwargs_typed_list(hi: Callable, cli_args: list[str]):
    check_args(hi, cli_args, ["hello", 3], {"arg_a": [1.0, 2.1]})


def test_var_args_kwargs_typed():
    check_args(
        hi_w_args_kwargs_typed,
        ["hello", "3"],
        ["hello", 3],
        {},
    )
    check_args(
        hi_w_args_kwargs_typed,
        ["hello", "3", "1", "2", "--arg-a=1.0", "--arg-b=2.1"],
        ["hello", 3, 1, 2],
        {"arg_a": 1.0, "arg_b": 2.1},
    )
    check_args(
        hi_w_args_kwargs_typed,
        ["hello", "3", "1", "2", "--arg-a=1.0", "--arg-b=2.1", "3"],
        ["hello", 3, 1, 2, 3],
        {"arg_a": 1.0, "arg_b": 2.1},
    )
    check_args(
        hi_w_args_kwargs_typed,
        ["hello", "3", "1", "2", "3", "--arg-a=1.0", "--arg-b", "2.1"],
        ["hello", 3, 1, 2, 3],
        {"arg_a": 1.0, "arg_b": 2.1},
    )
    check_args(
        hi_w_args_kwargs_typed,
        ["hello", "3", "1", "2", "--arg-a=1.0", "--arg-b", "2.1", "3"],
        ["hello", 3, 1, 2, 3],
        {"arg_a": 1.0, "arg_b": 2.1},
    )
    with raises(ParserValueError, match="Cannot parse integer from `a3`!"):
        check_args(
            hi_w_args_kwargs_typed,
            ["hello", "3", "1", "2", "a3", "--arg-a=1.0", "--arg-b", "2.1"],
            [],
            {},
        )
    with raises(ParserValueError, match="Cannot parse float from `1.0a`!"):
        check_args(
            hi_w_args_kwargs_typed,
            ["hello", "3", "1", "2", "3", "--arg-a=1.0a", "--arg-b", "2.1"],
            [],
            {},
        )
    with raises(ParserValueError, match="Cannot parse float from `2.1b`!"):
        check_args(
            hi_w_args_kwargs_typed,
            ["hello", "3", "1", "2", "3", "--arg-a=1.0", "--arg-b", "2.1b"],
            [],
            {},
        )
