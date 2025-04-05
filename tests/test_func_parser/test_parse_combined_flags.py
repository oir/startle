import re

from pytest import raises

from startle.error import ParserOptionError

from ._utils import check_args


def jolt(
    name: str = "jolt", *, alpha: bool = False, beta: bool = False, gamma: bool = False
):
    """
    A function that takes a name and three boolean flags.

    Args:
        name (str): The name to use.
        alpha (bool): The alpha flag.
        beta (bool): The beta flag.
        gamma (bool): The gamma flag.
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


def test_flags_with_unary():
    check_args(
        jolt, ["-an", "zap"], ["zap"], {"alpha": True, "beta": False, "gamma": False}
    )
    check_args(
        jolt, ["-abn", "zap"], ["zap"], {"alpha": True, "beta": True, "gamma": False}
    )
    check_args(
        jolt, ["-abgn", "zap"], ["zap"], {"alpha": True, "beta": True, "gamma": True}
    )
    check_args(
        jolt, ["-gn", "zap"], ["zap"], {"alpha": False, "beta": False, "gamma": True}
    )
    check_args(
        jolt, ["-gbn", "zap"], ["zap"], {"alpha": False, "beta": True, "gamma": True}
    )
    check_args(
        jolt, ["-gban", "zap"], ["zap"], {"alpha": True, "beta": True, "gamma": True}
    )
    check_args(
        jolt,
        ["-gb", "-an", "zap"],
        ["zap"],
        {"alpha": True, "beta": True, "gamma": True},
    )

    check_args(
        jolt, ["-an=zap"], ["zap"], {"alpha": True, "beta": False, "gamma": False}
    )
    check_args(
        jolt, ["-abn=zap"], ["zap"], {"alpha": True, "beta": True, "gamma": False}
    )
    check_args(
        jolt, ["-abgn=zap"], ["zap"], {"alpha": True, "beta": True, "gamma": True}
    )
    check_args(
        jolt, ["-gn=zap"], ["zap"], {"alpha": False, "beta": False, "gamma": True}
    )
    check_args(
        jolt, ["-gbn=zap"], ["zap"], {"alpha": False, "beta": True, "gamma": True}
    )
    check_args(
        jolt, ["-gban=zap"], ["zap"], {"alpha": True, "beta": True, "gamma": True}
    )
    check_args(
        jolt, ["-gb", "-an=zap"], ["zap"], {"alpha": True, "beta": True, "gamma": True}
    )

    with raises(
        ParserOptionError, match=re.escape("Option `name` is missing argument!")
    ):
        check_args(jolt, ["-an"], [], {})
