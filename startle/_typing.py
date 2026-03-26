import inspect
import sys
import types
from collections.abc import Iterable, MutableSequence, MutableSet, Sequence
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Optional,
    TypeAlias,
    TypeGuard,
    Union,
    cast,
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


def normalize(hint: TypeHint) -> TypeHint:
    """
    Normalize a type annotation by stripping Annotated, resolving type aliases,
    and unifying Union and Optional types.
    """
    prev: Any = None
    curr: Any = hint
    while prev != curr:
        prev = curr
        curr = strip_annotated(curr)
        curr = resolve_type_alias(curr)
        curr = normalize_union_type(curr)
    return curr


def shorten(hint: TypeHint) -> str:
    """
    Shorten a type annotation for error messages.
    """
    origin = get_origin(hint)
    if origin is None:
        # It's a simple type, return its name
        if inspect.isclass(hint):
            return hint.__name__
        return repr(hint)

    if origin is Union or origin is types.UnionType:
        args = get_args(hint)
        if type(None) in args:
            args = tuple([arg for arg in args if arg is not type(None)])
            if len(args) == 1:
                return f"{shorten(args[0])} | None"
            return " | ".join(shorten(arg) for arg in args) + " | None"
        else:
            return " | ".join(shorten(arg) for arg in args)

    # It's a generic type, process its arguments
    args = get_args(hint)
    if args:
        args_str = ", ".join(shorten(arg) for arg in args)
        return f"{origin.__name__}[{args_str}]"

    return repr(hint)


def is_typeddict(type_: TypeHint) -> TypeGuard[type[dict[str, Any]]]:
    """
    Return True if the given type hint is a TypedDict class.
    """

    # we only use __annotations__, so merely checking for that
    # and dict subclassing. TODO: maybe narrow this down further?
    return (
        isinstance(type_, type)
        and issubclass(type_, dict)
        and hasattr(type_, "__annotations__")  # type: ignore
    )


def strip_container(hint: "TypeHint | type") -> tuple[type | None, Any]:
    """
    Split a sequential container type hint into its container type and inner type.
    For example, given list[int], return (list, int).
    If inner type is absent from the hint, assumes `str`.

    Returns:
        `container type`, and `inner type` as a tuple.
    """
    orig = get_origin(hint)
    args_ = get_args(hint)

    if orig in [list, set, frozenset]:
        return orig, normalize(args_[0]) if args_ else str
    if orig is tuple and len(args_) == 2 and args_[1] is ...:
        return orig, normalize(args_[0]) if args_ else str
    if orig is tuple and not args_:
        return orig, str
    if hint in [list, tuple, set, frozenset]:
        container_type = cast(type, hint)
        return container_type, str

    # handle abstract collections
    if orig in [MutableSequence]:
        return list, normalize(args_[0]) if args_ else str
    if hint in [MutableSequence]:
        return list, str

    if orig in [Sequence, Iterable]:
        return tuple, normalize(args_[0]) if args_ else str
    if hint in [Sequence, Iterable]:
        return tuple, str

    if orig in [MutableSet]:
        return set, normalize(args_[0]) if args_ else str
    if hint in [MutableSet]:
        return set, str

    return None, hint
