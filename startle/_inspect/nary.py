from collections.abc import Iterable, MutableSequence, MutableSet, Sequence
from typing import Any, cast, get_args, get_origin

from .._typing import strip_annotated


def get_annotation_naryness(
    normalized_annotation: Any,
) -> tuple[bool, type | None, Any]:
    """
    Get the n-ary status, container type, and normalized annotation for an annotation.
    For n-ary parameters, the type (updated `normalized_annotation`) will refer
    to the inner type.

    If inner type is absent from the hint, assume str.

    Returns:
        `nary`, `container_type`, and `normalized_annotation` as a tuple.
    """
    orig = get_origin(normalized_annotation)
    args_ = get_args(normalized_annotation)

    if orig in [list, set, frozenset]:
        return True, orig, strip_annotated(args_[0]) if args_ else str
    if orig is tuple and len(args_) == 2 and args_[1] is ...:
        return True, orig, strip_annotated(args_[0]) if args_ else str
    if orig is tuple and not args_:
        return True, orig, str
    if normalized_annotation in [list, tuple, set, frozenset]:
        container_type = cast(type, normalized_annotation)
        return True, container_type, str

    # handle abstract collections
    if orig in [MutableSequence]:
        return True, list, strip_annotated(args_[0]) if args_ else str
    if normalized_annotation in [MutableSequence]:
        return True, list, str

    if orig in [Sequence, Iterable]:
        return True, tuple, strip_annotated(args_[0]) if args_ else str
    if normalized_annotation in [Sequence, Iterable]:
        return True, tuple, str

    if orig in [MutableSet]:
        return True, set, strip_annotated(args_[0]) if args_ else str
    if normalized_annotation in [MutableSet]:
        return True, set, str

    return False, None, normalized_annotation
