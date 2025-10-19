import re
from typing import Annotated

from pytest import mark, raises

from startle._inspect.make_args import make_args_from_func
from startle.error import ParserConfigError, ParserOptionError, ParserValueError

from ._utils import check_args


def hi_int(name: str = "john", /, *, count: int = 1) -> None:
    for _ in range(count):
        print(f"hello, {name}!")


def hi_float(name: str = "john", /, *, count: float = 1.0) -> None:
    for _ in range(int(count)):
        print(f"hello, {name}!")


def hi_float_annotated(
    name: Annotated[str, "some metadata"] = "john",
    /,
    *,
    count: Annotated[float, "some metadata"] = 1.0,
) -> None:
    for _ in range(int(count)):
        print(f"hello, {name}!")


@mark.parametrize(
    "hi, count_t", [(hi_int, int), (hi_float, float), (hi_float_annotated, float)]
)
def test_args_with_defaults(hi, count_t):
    typestr = "integer" if count_t is int else "float"

    check_args(hi, [], ["john"], {"count": count_t(1)})
    check_args(hi, ["jane"], ["jane"], {"count": count_t(1)})
    check_args(hi, ["jane", "--count", "3"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["jane", "--count=3"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["--count", "3", "jane"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["--count", "3", "--", "jane"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["--count", "3"], ["john"], {"count": count_t(3)})
    check_args(hi, ["--count", "3", "--"], ["john"], {"count": count_t(3)})
    check_args(hi, ["jane", "-c", "3"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["jane", "-c=3"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["-c", "3", "jane"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["-c", "3", "--", "jane"], ["jane"], {"count": count_t(3)})
    check_args(hi, ["-c", "3"], ["john"], {"count": count_t(3)})

    with raises(ParserValueError, match=f"Cannot parse {typestr} from `x`!"):
        check_args(hi, ["jane", "--count", "x"], [], {})
    with raises(ParserValueError, match=f"Cannot parse {typestr} from `x`!"):
        check_args(hi, ["--count", "x", "jane"], [], {})
    with raises(ParserValueError, match=f"Cannot parse {typestr} from `x`!"):
        check_args(hi, ["--count", "x", "--", "jane"], [], {})
    with raises(ParserValueError, match=f"Cannot parse {typestr} from `x`!"):
        check_args(hi, ["jane", "--count=x"], [], {})

    with raises(ParserOptionError, match="Unexpected positional argument: `3`!"):
        check_args(hi, ["john", "3"], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `3`!"):
        check_args(hi, ["john", "--", "3"], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `3`!"):
        check_args(hi, ["--", "john", "3"], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `--`!"):
        # Second `--` will be treated as a positional argument as is
        check_args(hi, ["--", "john", "--", "3"], [], {})

    with raises(ParserOptionError, match="Option `count` is missing argument!"):
        check_args(hi, ["--count"], [], {})
    with raises(ParserOptionError, match="Option `count` is missing argument!"):
        check_args(hi, ["jane", "--count"], [], {})

    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["--name", "jane"], [], {})
    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["--name", "jane", "john"], [], {})
    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["john", "--name", "jane"], [], {})
    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["--name=jane"], [], {})

    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["john", "--count", "3", "--count", "4"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["john", "--count", "3", "-c", "4"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["john", "--count=3", "--count", "4"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["john", "--count", "3", "--count=4"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["--count", "3", "john", "--count", "4"], [], {})

    # with raises(ParserOptionError, match="Prefix `--` is not followed by an option!"):
    #    check_args(hi, ["john", "-c", "3", "--"], [], {})
    with raises(ParserOptionError, match="Prefix `-` is not followed by an option!"):
        check_args(hi, ["john", "-"], [], {})


@mark.parametrize("opt", ["-c", "--count"])
def test_args_without_defaults(opt):
    def hi(name: str, /, *, count: int) -> None:
        for _ in range(count):
            print(f"hello, {name}!")

    check_args(hi, ["jane", opt, "3"], ["jane"], {"count": 3})
    check_args(hi, [opt, "3", "jane"], ["jane"], {"count": 3})
    check_args(hi, [opt, "3", "--", "jane"], ["jane"], {"count": 3})
    check_args(hi, ["jane", f"{opt}=3"], ["jane"], {"count": 3})
    check_args(hi, [f"{opt}=3", "jane"], ["jane"], {"count": 3})
    check_args(hi, [f"{opt}=3", "--", "jane"], ["jane"], {"count": 3})

    with raises(
        ParserOptionError, match="Required positional argument <name> is not provided!"
    ):
        check_args(hi, [], [], {})
    with raises(ParserOptionError, match="Required option `count` is not provided!"):
        check_args(hi, ["jane"], [], {})
    with raises(ParserOptionError, match="Required option `count` is not provided!"):
        check_args(hi, ["--", "jane"], [], {})
    with raises(
        ParserOptionError, match="Required positional argument <name> is not provided!"
    ):
        check_args(hi, [opt, "3"], [], {})

    with raises(ParserOptionError, match="Unexpected positional argument: `jane`!"):
        check_args(hi, ["jane", "jane", opt, "3"], [], {})
    with raises(ParserOptionError, match="Option `count` is multiply given!"):
        check_args(hi, ["jane", opt, "3", "-c", "4"], [], {})

    with raises(ParserOptionError, match="Unexpected positional argument: `3`!"):
        check_args(hi, ["jane", "3"], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `3`!"):
        check_args(hi, ["jane", "--", "3"], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `3`!"):
        check_args(hi, ["--", "jane", "3"], [], {})

    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["--name", "jane"], [], {})
    with raises(ParserOptionError, match="Unexpected option `name`!"):
        check_args(hi, ["jane", "--name", "jane"], [], {})


@mark.parametrize(
    "person_name_opt",
    [
        ["jane"],
        ["--person-name", "jane"],
        ["--person_name", "jane"],
        ["--person-name=jane"],
        ["--person_name=jane"],
        ["-p", "jane"],
        ["-p=jane"],
    ],
)
@mark.parametrize(
    "hello_count_opt",
    [
        ["3"],
        ["--hello-count", "3"],
        ["--hello_count", "3"],
        ["--hello-count=3"],
        ["--hello_count=3"],
        ["-h", "3"],
        ["-h=3"],
    ],
)
def test_args_both_positional_and_keyword(person_name_opt, hello_count_opt):
    def hi(person_name: str, hello_count: int) -> None:
        for _ in range(hello_count):
            print(f"hello, {person_name}!")

    check_args(hi, [*person_name_opt, *hello_count_opt], ["jane", 3], {})

    with raises(ParserOptionError, match="Option `person-name` is multiply given!"):
        check_args(
            hi, [*person_name_opt, "--person-name", "john", *hello_count_opt], [], {}
        )
    with raises(ParserOptionError, match="Option `person-name` is multiply given!"):
        check_args(
            hi, [*person_name_opt, "--person_name", "john", *hello_count_opt], [], {}
        )
    with raises(ParserOptionError, match="Option `person-name` is multiply given!"):
        check_args(
            hi, [*person_name_opt, "--person-name=john", *hello_count_opt], [], {}
        )
    with raises(ParserOptionError, match="Option `person-name` is multiply given!"):
        check_args(
            hi, [*person_name_opt, "--person_name=john", *hello_count_opt], [], {}
        )

    with raises(ParserOptionError, match="Unexpected positional argument: `4`!"):
        check_args(hi, [*person_name_opt, *hello_count_opt, "4"], [], {})


def test_args_both_positional_and_keyword_with_defaults():
    def hi(name: str = "john", count: int = 1) -> None:
        for _ in range(count):
            print(f"hello, {name}!")

    check_args(hi, [], ["john", 1], {})

    check_args(hi, ["jane"], ["jane", 1], {})
    check_args(hi, ["--name", "jane"], ["jane", 1], {})

    check_args(hi, ["jane", "3"], ["jane", 3], {})
    check_args(hi, ["--", "jane", "3"], ["jane", 3], {})
    check_args(hi, ["jane", "--", "3"], ["jane", 3], {})
    check_args(hi, ["jane", "--count", "3"], ["jane", 3], {})
    check_args(hi, ["--name", "jane", "--count", "3"], ["jane", 3], {})
    check_args(hi, ["--name", "jane", "3"], ["jane", 3], {})
    check_args(hi, ["--name", "jane", "--", "3"], ["jane", 3], {})
    check_args(hi, ["--count", "3", "--name", "jane"], ["jane", 3], {})
    check_args(hi, ["--count", "3", "jane"], ["jane", 3], {})
    check_args(hi, ["--count", "3", "--", "jane"], ["jane", 3], {})

    check_args(hi, ["--count", "3"], ["john", 3], {})


@mark.parametrize("opt", ["-v", "--verbose"])
def test_flag(opt):
    def hi(name: str, /, *, verbose: bool = False) -> None:
        print(f"hello, {name}!")
        if verbose:
            print("verbose mode")

    check_args(hi, ["jane"], ["jane"], {"verbose": False})
    check_args(hi, ["jane", opt], ["jane"], {"verbose": True})
    check_args(hi, [opt, "jane"], ["jane"], {"verbose": True})
    check_args(hi, [opt, "--", "jane"], ["jane"], {"verbose": True})
    with raises(
        ParserOptionError, match="Required positional argument <name> is not provided!"
    ):
        check_args(hi, [opt], [], {})
    with raises(ParserOptionError, match="Unexpected positional argument: `true`!"):
        check_args(hi, ["jane", opt, "true"], [], {})
    with raises(ParserOptionError, match="Option `verbose` is multiply given!"):
        check_args(hi, ["jane", opt, opt], [], {})
    with raises(
        ParserOptionError,
        match="Option `verbose` is a flag and cannot be assigned a value!",
    ):
        check_args(hi, ["jane", f"{opt}=true"], [], {})


@mark.parametrize(
    "true", ["true", "True", "TRUE", "t", "T", "yes", "Yes", "YES", "y", "Y", "1"]
)
@mark.parametrize(
    "false", ["false", "False", "FALSE", "f", "F", "no", "No", "NO", "n", "N", "0"]
)
@mark.parametrize("optv", ["-v", "--verbose"])
@mark.parametrize("optn", ["-n", "--name"])
def test_bool_but_not_flag(true: str, false: str, optv: str, optn: str):
    def hi(name: str, /, *, verbose: bool = True) -> None:
        print(f"hello, {name}!")
        if verbose:
            print("verbose mode")

    check_args(hi, ["jane"], ["jane"], {"verbose": True})
    for verbose in [True, False]:
        value = true if verbose else false
        check_args(hi, ["jane", optv, value], ["jane"], {"verbose": verbose})
        check_args(hi, [optv, value, "jane"], ["jane"], {"verbose": verbose})
        check_args(hi, [optv, value, "--", "jane"], ["jane"], {"verbose": verbose})
        check_args(hi, ["jane", f"{optv}={value}"], ["jane"], {"verbose": verbose})
        check_args(hi, [f"{optv}={value}", "jane"], ["jane"], {"verbose": verbose})
        check_args(
            hi, [f"{optv}={value}", "--", "jane"], ["jane"], {"verbose": verbose}
        )
    with raises(ParserOptionError, match="Option `verbose` is missing argument!"):
        check_args(hi, ["jane", optv], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `yeah`!"):
        check_args(hi, ["jane", optv, "yeah"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `yeah`!"):
        check_args(hi, ["jane", f"{optv}=yeah"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `nah`!"):
        check_args(hi, [optv, "nah", "jane"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `nah`!"):
        check_args(hi, [f"{optv}=nah", "jane"], [], {})

    def hi2(name: str, verbose: bool = False, /) -> None:
        print(f"hello, {name}!")
        if verbose:
            print("verbose mode")

    check_args(hi2, ["jane"], ["jane", False], {})
    check_args(hi2, ["jane", true], ["jane", True], {})
    check_args(hi2, ["jane", false], ["jane", False], {})

    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi2, ["jane", "maybe"], [], {})

    def hi3(name: str, verbose: bool) -> None:
        print(f"hello, {name}!")
        if verbose:
            print("verbose mode")

    for verbose in [True, False]:
        value = true if verbose else false
        check_args(hi3, ["jane", value], ["jane", verbose], {})
        check_args(hi3, [optn, "jane", value], ["jane", verbose], {})
        check_args(hi3, ["jane", optv, value], ["jane", verbose], {})
        check_args(hi3, [optv, value, "jane"], ["jane", verbose], {})
        check_args(hi3, [optn, "jane", optv, value], ["jane", verbose], {})
        check_args(hi3, [optv, value, optn, "jane"], ["jane", verbose], {})

    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi3, ["jane", "maybe"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi3, ["jane", optv, "maybe"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi3, ["jane", f"{optv}=maybe"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi3, [optv, "maybe", "jane"], [], {})
    with raises(ParserValueError, match="Cannot parse boolean from `maybe`!"):
        check_args(hi3, [f"{optv}=maybe", "jane"], [], {})


def test_pathlib_path():
    from pathlib import Path

    def transfer(destination: Path, source: Path = Path("./")) -> None:
        print(f"Transferring from {source} to {destination}.")

    check_args(
        transfer,
        ["./destination", "./source"],
        [Path("./destination"), Path("./source")],
        {},
    )
    check_args(
        transfer,
        ["./destination"],
        [Path("./destination"), Path("./")],
        {},
    )
    check_args(
        transfer,
        ["./destination", "--source", "./source"],
        [Path("./destination"), Path("./source")],
        {},
    )
    check_args(
        transfer,
        ["--source", "./source", "./destination"],
        [Path("./destination"), Path("./source")],
        {},
    )
    check_args(
        transfer,
        ["--source", "./source", "--destination", "./destination"],
        [Path("./destination"), Path("./source")],
        {},
    )

    with raises(
        ParserOptionError,
        match="Required option `destination` is not provided!",
    ):
        check_args(transfer, [], [], {})
    with raises(ParserOptionError, match="Option `destination` is missing argument!"):
        check_args(transfer, ["--destination"], [], {})
    with raises(ParserOptionError, match="Option `destination` is multiply given!"):
        check_args(
            transfer, ["./destination", "--destination", "./destination"], [], {}
        )


def hi_help(help: str = "help", count: int = 3) -> None:
    print(f"{help}!")


def test_param_named_help():
    with raises(
        ParserConfigError,
        match=re.escape(
            f"Cannot use `help` as parameter name in `{hi_help.__name__}()`!"
        ),
    ):
        make_args_from_func(hi_help)


def hi_untyped(name, count) -> None:
    print(f"hello, {name}!")
    print(f"count: {count}")


def test_untyped():
    check_args(hi_untyped, ["jane", "3"], ["jane", "3"], {})
    check_args(hi_untyped, ["jane", "--", "3"], ["jane", "3"], {})
    check_args(hi_untyped, ["--", "jane", "3"], ["jane", "3"], {})
    check_args(hi_untyped, ["jane", "--count", "3"], ["jane", "3"], {})
    check_args(hi_untyped, ["--count", "3", "jane"], ["jane", "3"], {})
    check_args(hi_untyped, ["--count", "3", "--", "jane"], ["jane", "3"], {})
    check_args(hi_untyped, ["--name", "jane", "--count", "3"], ["jane", "3"], {})
    check_args(hi_untyped, ["-n", "jane", "-c", "3"], ["jane", "3"], {})
