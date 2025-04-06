import re

from pytest import mark, raises

from startle.error import ParserOptionError

from ._utils import check_args


def jolt(
    name: str = "jolt", *, alpha: bool = False, beta: bool = False, gamma: bool = False
):
    """
    A function that takes a name and three boolean flags.

    Args:
        name: The name to use.
        alpha: The alpha flag.
        beta: The beta flag.
        gamma: The gamma flag.
    """
    pass


def test_only_flags():
    check_args(jolt, ["-a"], ["jolt"], {"alpha": True, "beta": False, "gamma": False})
    check_args(jolt, ["-ab"], ["jolt"], {"alpha": True, "beta": True, "gamma": False})
    check_args(jolt, ["-abg"], ["jolt"], {"alpha": True, "beta": True, "gamma": True})
    check_args(jolt, ["-g"], ["jolt"], {"alpha": False, "beta": False, "gamma": True})
    check_args(jolt, ["-gb"], ["jolt"], {"alpha": False, "beta": True, "gamma": True})
    check_args(jolt, ["-gba"], ["jolt"], {"alpha": True, "beta": True, "gamma": True})
    check_args(
        jolt, ["-gb", "-a"], ["jolt"], {"alpha": True, "beta": True, "gamma": True}
    )

    with raises(
        ParserOptionError,
        match=re.escape("Option `name` is not a flag and cannot be combined!"),
    ):
        check_args(jolt, ["-anb"], [], {})
    with raises(ParserOptionError, match=re.escape("Unexpected option `k`!")):
        check_args(jolt, ["-abk"], [], {})
    with raises(ParserOptionError, match=re.escape("Option `beta` is multiply given!")):
        check_args(jolt, ["-abgb"], [], {})


@mark.parametrize("alpha", [True, False])
@mark.parametrize("beta", [True, False])
@mark.parametrize("gamma", [True, False])
def test_flags_with_unary(alpha: bool, beta: bool, gamma: bool):
    argstr = "-"
    if alpha:
        argstr += "a"
    if beta:
        argstr += "b"
    if gamma:
        argstr += "g"
    argstr += "n"
    check_args(
        jolt, [argstr, "zap"], ["zap"], {"alpha": alpha, "beta": beta, "gamma": gamma}
    )
    if len(argstr) > 3:
        argstr1, argstr2 = argstr[:2], f"-{argstr[2:]}"
        check_args(
            jolt,
            [argstr1, argstr2, "zap"],
            ["zap"],
            {"alpha": alpha, "beta": beta, "gamma": gamma},
        )

    with raises(
        ParserOptionError, match=re.escape("Option `name` is missing argument!")
    ):
        check_args(jolt, [argstr], [], {})

    argstr = f"{argstr}=zap"
    check_args(jolt, [argstr], ["zap"], {"alpha": alpha, "beta": beta, "gamma": gamma})


def jolt_multi(
    names: list[str] = ["jolt"],
    *,
    alpha: bool = False,
    beta: bool = False,
    gamma: bool = False,
):
    """
    A function that takes a name and three boolean flags.

    Args:
        names: Names to use.
        alpha: The alpha flag.
        beta: The beta flag.
        gamma: The gamma flag.
    """
    pass


@mark.parametrize("alpha", [True, False])
@mark.parametrize("beta", [True, False])
@mark.parametrize("gamma", [True, False])
@mark.parametrize("names", [["zap"], ["zap", "zop"]])
def test_flags_with_nary(alpha: bool, beta: bool, gamma: bool, names: list[str]):
    argstr = "-"
    if alpha:
        argstr += "a"
    if beta:
        argstr += "b"
    if gamma:
        argstr += "g"
    argstr += "n"
    check_args(
        jolt_multi,
        [argstr, *names],
        [names],
        {"alpha": alpha, "beta": beta, "gamma": gamma},
    )
    if len(argstr) > 3:
        argstr1, argstr2 = argstr[:2], f"-{argstr[2:]}"
        check_args(
            jolt_multi,
            [argstr1, argstr2, *names],
            [names],
            {"alpha": alpha, "beta": beta, "gamma": gamma},
        )

    with raises(
        ParserOptionError, match=re.escape("Option `names` is missing argument!")
    ):
        check_args(jolt_multi, [argstr], [], {})

    argstr = f"{argstr}=zap"
    check_args(
        jolt_multi, [argstr], [["zap"]], {"alpha": alpha, "beta": beta, "gamma": gamma}
    )
