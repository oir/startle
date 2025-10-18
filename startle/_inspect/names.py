from inspect import Parameter
from typing import Iterable

from .._docstr import _DocstrParams
from .._type_utils import TypeHint


def _reserve_short_names(
    params: Iterable[tuple[str, Parameter | TypeHint]],
    used_names: list[str],
    arg_helps: _DocstrParams = {},
    used_short_names: set[str] | None = None,
) -> set[str]:
    def is_kw(param_or_annot: Parameter | TypeHint) -> bool:
        # is non-variadic keyword parameter
        if isinstance(param_or_annot, Parameter):
            return param_or_annot.kind in [
                Parameter.KEYWORD_ONLY,
                Parameter.POSITIONAL_OR_KEYWORD,
            ]
        else:
            return True  # TypeHint is always keyword

    used_short_names = used_short_names or set()

    # Discover if there are any named options that are of length 1
    # If so, those cannot be used as short names for other options
    for name in used_names:
        if len(name) == 1:
            used_short_names.add(name)

    # Discover if there are any docstring-specified short names,
    # these also take precedence over the first letter of the parameter name
    for name, param_or_annot in params:
        if is_kw(param_or_annot):
            if docstr_param := arg_helps.get(name):
                if docstr_param.short_name:
                    # if this name is already used, this param cannot use it
                    if docstr_param.short_name in used_short_names:
                        docstr_param.short_name = None
                    else:
                        used_short_names.add(docstr_param.short_name)

    return used_short_names
