import inspect
import sys
import types
from typing import Annotated, Any, Optional, Union, get_args, get_origin, TypedDict


def _strip_optional(type_: Any) -> Any:
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


def _strip_annotated(type_: Any) -> Any:
    """
    Strip the Annotated type from a type hint. Given Annotated[T, ...], return T.
    """
    if get_origin(type_) is Annotated:
        args = get_args(type_)
        if args:
            return args[0]
    return type_


def _resolve_type_alias(type_: Any) -> Any:
    """
    Resolve type aliases to their underlying types.
    """
    if sys.version_info >= (3, 12):
        from typing import TypeAliasType

        if isinstance(type_, TypeAliasType):
            return type_.__value__
    return type_


def _normalize_union_type(annotation: Any) -> Any:
    """
    Normalize a type annotation by unifying Union and Optional types.
    """
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is Union or origin is types.UnionType:
        if type(None) in args:
            args = tuple([arg for arg in args if arg is not type(None)])
            if len(args) == 1:
                return Optional[args[0]]
            else:
                return Union[args + tuple([type(None)])]
        else:
            return Union[tuple(args)]
    return annotation


def _normalize_type(annotation: Any) -> Any:
    """
    Normalize a type annotation by stripping Annotated, resolving type aliases,
    and unifying Union and Optional types.
    """
    prev: Any = None
    curr: Any = annotation
    while prev != curr:
        prev = curr
        curr = _strip_annotated(curr)
        curr = _resolve_type_alias(curr)
        curr = _normalize_union_type(curr)
    return curr


def _shorten_type_annotation(annotation: Any) -> str:
    origin = get_origin(annotation)
    if origin is None:
        # It's a simple type, return its name
        if inspect.isclass(annotation):
            return annotation.__name__
        return repr(annotation)

    if origin is Union or origin is types.UnionType:
        args = get_args(annotation)
        if type(None) in args:
            args = tuple([arg for arg in args if arg is not type(None)])
            if len(args) == 1:
                return f"{_shorten_type_annotation(args[0])} | None"
            return " | ".join(_shorten_type_annotation(arg) for arg in args) + " | None"
        else:
            return " | ".join(_shorten_type_annotation(arg) for arg in args)

    # It's a generic type, process its arguments
    args = get_args(annotation)
    if args:
        args_str = ", ".join(_shorten_type_annotation(arg) for arg in args)
        return f"{origin.__name__}[{args_str}]"

    return repr(annotation)


def _is_typeddict(type_: type) -> bool:
    """
    Return True if the given type is a TypedDict class.
    """

    # we only use __annotations__, so merely checking for that
    # and dict subclassing
    return (
        isinstance(type_, type)
        and issubclass(type_, dict)
        and hasattr(type_, "__annotations__")
    )