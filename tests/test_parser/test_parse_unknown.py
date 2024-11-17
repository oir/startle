from _utils import check_args
from pytest import mark, raises

from startle.error import ParserOptionError


def hi_w_args(msg: str, n: int, *args) -> None:
    pass


def hi_w_kwargs(msg: str, n: int, **kwargs) -> None:
    pass


@mark.parametrize("unks", [[], ["arg1"], ["arg1", "arg2"], ["arg1", "arg2", "arg3"]])
def test_var_args(unks: list[str]):
    check_args(
        hi_w_args,
        ["hello", "3", *unks],
        ["hello", 3, *unks],
        {},
    )


@mark.parametrize("unks", [{}, {"arg-a": "val1"}, {"arg-a": "val1", "arg-b": "val2"}])
def test_var_kwargs(unks: dict[str, str]):
    check_args(
        hi_w_kwargs,
        ["hello", "3"] + [f"--{k}={v}" for k, v in unks.items()],
        ["hello", 3],
        {k.replace("-", "_"): v for k, v in unks.items()},
    )


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
def test_var_kwargs_list(cli_args: list[str]):
    check_args(hi_w_kwargs, cli_args, ["hello", 3], {"arg_a": ["val1", "val2"]})


def test_var_kwargs_errors():
    with raises(ParserOptionError, match="Option `arg-a` is missing argument!"):
        check_args(hi_w_kwargs, ["hello", "3", "--arg-a"], [], {})
    with raises(ParserOptionError, match="Option `arg-a` is missing argument!"):
        check_args(hi_w_kwargs, ["hello", "3", "--arg-a", "--arg-b"], [], {})
    with raises(ParserOptionError, match="Required option `msg` is not provided!"):
        check_args(hi_w_kwargs, ["--arg-a", "val1", "val2", "hello", "3"], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `world`!"):
        # because there is kwargs, but not args, the following is invalid
        check_args(
            hi_w_kwargs, ["hello", "--arg-a=val1", "--arg-a=val2", "3", "world"], [], {}
        )
