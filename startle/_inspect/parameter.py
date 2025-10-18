from inspect import Parameter


def _is_positional(param: Parameter) -> bool:
    return param.kind in [
        Parameter.POSITIONAL_ONLY,
        Parameter.POSITIONAL_OR_KEYWORD,
        Parameter.VAR_POSITIONAL,
    ]


def _is_keyword(param: Parameter) -> bool:
    return param.kind in [
        Parameter.KEYWORD_ONLY,
        Parameter.POSITIONAL_OR_KEYWORD,
        Parameter.VAR_KEYWORD,
    ]


def _is_variadic(param: Parameter) -> bool:
    return param.kind in [Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD]
