from inspect import Parameter
from typing import Any

from .._type_utils import shorten_type_annotation, strip_optional
from ..error import (
    NaryNonRecursableParamError,
    NonClassNonRecursableParamError,
    VariadicNonRecursableParamError,
)
from .parameter import is_variadic


def check_recursable(
    param_name: str,
    param: Parameter,
    normalized_annotation: Any,
    obj_name: str,
    nary: bool,
) -> None:
    """
    Raise if the given parameter cannot be recursed into, no-op otherwise.
    """
    if is_variadic(param):
        raise VariadicNonRecursableParamError(param_name, obj_name)
    if nary:
        raise NaryNonRecursableParamError(param_name, obj_name)
    normalized_annotation = strip_optional(normalized_annotation)
    if not isinstance(normalized_annotation, type):
        raise NonClassNonRecursableParamError(
            param_name, shorten_type_annotation(param.annotation), obj_name
        )
