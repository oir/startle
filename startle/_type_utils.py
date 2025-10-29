import inspect
import sys
import types
from inspect import Parameter
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Optional,
    TypeAlias,
    Union,
    get_args,
    get_origin,
)

if TYPE_CHECKING:
    from typing_extensions import TypeForm

TypeHint: TypeAlias = "TypeForm[Any]"


def strip_optional(type_: TypeHint) -> TypeHint:
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
                return Union[args]  # type: ignore

    return type_


def _strip_unary_outer(type_: TypeHint, outer: Any) -> tuple[bool, TypeHint]:
    """
    Strip a unary outer type from a type hint. If given outer[T], return (True, T).
    Otherwise, return (False, type_).
    """
    if outer is None:
        return False, type_
    if get_origin(type_) is outer:
        args = get_args(type_)
        if args:
            return True, args[0]
    return False, type_


def _required_t() -> Any:
    if sys.version_info >= (3, 11):
        from typing import Required as TypingRequired

        return TypingRequired
    try:
        from typing_extensions import Required as TE_Required

        return TE_Required
    except ImportError:
        return None


def _not_required_t() -> Any:
    if sys.version_info >= (3, 11):
        from typing import NotRequired as TypingNotRequired

        return TypingNotRequired
    try:
        from typing_extensions import NotRequired as TE_NotRequired

        return TE_NotRequired
    except ImportError:
        return None


def strip_not_required(type_: TypeHint) -> tuple[bool, TypeHint]:
    """
    Strip NotRequired from a type hint. If given a NotRequired[T], return (True, T).
    Otherwise, return (False, type_).
    """
    match, type_ = _strip_unary_outer(type_, outer=_not_required_t())
    if match:
        return True, type_
    return False, type_


def strip_required(type_: TypeHint) -> tuple[bool, TypeHint]:
    """
    Strip Required from a type hint. If given a Required[T], return (True, T).
    Otherwise, return (False, type_).
    """
    match, type_ = _strip_unary_outer(type_, outer=_required_t())
    if match:
        return True, type_
    return False, type_


def strip_annotated(type_: TypeHint) -> TypeHint:
    """
    Strip the Annotated type from a type hint. Given Annotated[T, ...], return T.
    """
    _, type_ = _strip_unary_outer(type_, outer=Annotated)
    return type_


def resolve_type_alias(type_: TypeHint) -> TypeHint:
    """
    Resolve type aliases to their underlying types.
    """
    if sys.version_info >= (3, 12):
        from typing import TypeAliasType

        if isinstance(type_, TypeAliasType):
            return type_.__value__
    return type_


def normalize_union_type(annotation: TypeHint) -> TypeHint:
    """
    Normalize a type annotation by unifying Union and Optional types.
    """
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is Union or origin is types.UnionType:
        if type(None) in args:
            args = tuple([arg for arg in args if arg is not type(None)])
            if len(args) == 1:
                return Optional[args[0]]  # type: ignore
            else:
                return Union[args + tuple([type(None)])]  # type: ignore
        else:
            return Union[tuple(args)]  # type: ignore
    return annotation


def normalize_type(annotation: TypeHint) -> TypeHint:
    """
    Normalize a type annotation by stripping Annotated, resolving type aliases,
    and unifying Union and Optional types.
    """
    prev: Any = None
    curr: Any = annotation
    while prev != curr:
        prev = curr
        curr = strip_annotated(curr)
        curr = resolve_type_alias(curr)
        curr = normalize_union_type(curr)
    return curr


def shorten_type_annotation(annotation: TypeHint) -> str:
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
                return f"{shorten_type_annotation(args[0])} | None"
            return " | ".join(shorten_type_annotation(arg) for arg in args) + " | None"
        else:
            return " | ".join(shorten_type_annotation(arg) for arg in args)

    # It's a generic type, process its arguments
    args = get_args(annotation)
    if args:
        args_str = ", ".join(shorten_type_annotation(arg) for arg in args)
        return f"{origin.__name__}[{args_str}]"

    return repr(annotation)


def is_typeddict(type_: type) -> bool:
    """
    Return True if the given type is a TypedDict class.
    """

    # we only use __annotations__, so merely checking for that
    # and dict subclassing. TODO: maybe narrow this down further?
    return (
        isinstance(type_, type)
        and issubclass(type_, dict)
        and hasattr(type_, "__annotations__")  # type: ignore
    )


def normalize_annotation(param_or_annot: "Parameter | TypeHint") -> Any:
    """
    Normalize a function parameter or type annotation.

    Args:
        param_or_annot: The function parameter or type annotation to normalize.
            If a Parameter is provided, its annotation will be used. If the
            annotation is empty, str will be assumed. If a TypeHint is provided,
            it will be normalized directly.
    """
    if isinstance(param_or_annot, Parameter):
        if param_or_annot.annotation is Parameter.empty:
            return str
        return normalize_type(param_or_annot.annotation)
    else:
        return normalize_type(param_or_annot)
