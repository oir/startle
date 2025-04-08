import inspect
import types
from typing import Any, Optional, Union, get_args, get_origin


def _strip_optional(type_: type):
    """
    Strip the Optional type from a type hint. Given T1 | ... | Tn | None,
    return T1 | ... | Tn.
    """
    if get_origin(type_) is Union:
        args = get_args(type_)
        if type(None) in args:
            args = tuple([arg for arg in args if arg is not type(None)])
            if len(args) == 1:
                return args[0]
            else:
                return Union[args]

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
                return Union[tuple(args + [type(None)])]
        else:
            return Union[tuple(args)]
    return annotation


def _shorten_type_annotation(annotation: Any) -> str:
    origin = get_origin(annotation)
    if origin is None:
        # It's a simple type, return its name
        if inspect.isclass(annotation):
            return annotation.__name__
        return str(annotation)

    # Handle Optional types explicitly
    if origin is Union or origin is types.UnionType:
        args = get_args(annotation)
        if type(None) in args:
            args = tuple([arg for arg in args if arg is not type(None)])
            if len(args) == 1:
                return f"{_shorten_type_annotation(args[0])} | None"
            return " | ".join(_shorten_type_annotation(arg) for arg in args) + " | None"

    # It's a generic type, process its arguments
    args = get_args(annotation)
    if args:
        args_str = ", ".join(_shorten_type_annotation(arg) for arg in args)
        return f"{origin.__name__}[{args_str}]"

    return str(annotation)
