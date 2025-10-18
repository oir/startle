from inspect import Parameter
from typing import Any

def _is_positional(kind: Any) -> bool:
    return kind in [
        Parameter.POSITIONAL_ONLY,
        Parameter.POSITIONAL_OR_KEYWORD,
        Parameter.VAR_POSITIONAL,
    ]


def _is_keyword(kind: Any) -> bool:
    return kind in [
        Parameter.KEYWORD_ONLY,
        Parameter.POSITIONAL_OR_KEYWORD,
        Parameter.VAR_KEYWORD,
    ]


def _is_variadic(kind: Any) -> bool:
    return kind in [Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD]


