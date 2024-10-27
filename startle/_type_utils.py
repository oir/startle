import types
import typing
from typing import Optional, Union, get_args, get_origin


def _strip_optional(type_: type) -> type:
    """
    Strip the Optional type from a type hint. Given T1 | ... | Tn | None,
    return T1 | ... | Tn.
    """
    if typing.get_origin(type_) is typing.Union:
        args = typing.get_args(type_)
        if type(None) in args:
            args = [arg for arg in args if arg is not type(None)]
            if len(args) == 1:
                return args[0]
            else:
                return typing.Union[tuple(args)]

    return type_


def _normalize_type(annotation):
    """
    Normalize a type annotation by unifying Union and Optional types.
    """
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is Union or origin is types.UnionType:
        if type(None) in args:
            args = [arg for arg in args if arg is not type(None)]
            if len(args) == 1:
                return Optional[args[0]]
            else:
                return Union[tuple(args)]
        else:
            return Union[tuple(args)]
    return annotation
