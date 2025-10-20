from collections.abc import Iterable
from inspect import Parameter
from typing import Any, Literal, cast, get_args, get_origin

from .._docstr import ParamHelp, ParamHelps
from .._type_utils import (
    TypeHint,
    is_typeddict,
    normalize_annotation,
    strip_annotated,
)
from .._value_parser import is_parsable
from ..arg import Name
from ..error import ParserConfigError
from .classes import get_class_initializer_params


def reserve_short_names(
    params: Iterable[tuple[str, "Parameter | TypeHint"]],
    used_names: list[str],
    arg_helps: ParamHelps = {},
    used_short_names: set[str] | None = None,
) -> set[str]:
    def is_kw(param_or_annot: "Parameter | TypeHint") -> bool:
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


def make_name(
    param_name_sub: str,
    named: bool,
    docstr_param: ParamHelp,
    used_short_names: set[str],
) -> Name:
    if named:
        if len(param_name_sub) == 1:
            return Name(short=param_name_sub)
        if docstr_param.short_name:
            # no need to check used_short_names, this name is already in there
            return Name(short=docstr_param.short_name, long=param_name_sub)
        if param_name_sub[0] not in used_short_names:
            used_short_names.add(param_name_sub[0])
            return Name(short=param_name_sub[0], long=param_name_sub)
    return Name(long=param_name_sub)


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

    if orig in [list, set]:
        return True, orig, strip_annotated(args_[0]) if args_ else str
    if orig is tuple and len(args_) == 2 and args_[1] is ...:
        return True, orig, strip_annotated(args_[0]) if args_ else str
    if normalized_annotation in [list, tuple, set]:
        container_type = cast(type, normalized_annotation)
        return True, container_type, str
    return False, None, normalized_annotation


def get_naryness(
    param_or_annot: "Parameter | TypeHint", normalized_annotation: Any
) -> tuple[bool, type | None, Any]:
    """
    Get the n-ary status, container type, and normalized annotation for a parameter.
    For n-ary parameters, the type (updated `normalized_annotation`) will refer
    to the inner type.

    If inner type is absent from the hint, assume str.

    Returns:
        `nary`, `container_type`, and `normalized_annotation` as a tuple.
    """
    if isinstance(param_or_annot, Parameter):
        if param_or_annot.kind is Parameter.VAR_POSITIONAL:
            return True, list, normalized_annotation

    return get_annotation_naryness(normalized_annotation)


def _get_params_or_annotations(
    annotation: type,
) -> Iterable[tuple[str, "Parameter | TypeHint"]]:
    if is_typeddict(annotation):
        return annotation.__annotations__.items()
    else:
        return get_class_initializer_params(annotation)


def collect_param_names(
    params: Iterable[tuple[str, "Parameter | TypeHint"]],
    obj_name: str,
    recurse: bool | Literal["child"] = False,
    kw_only: bool = False,
) -> list[str]:
    """
    Get all parameter names in the object hierarchy.
    This is used to detect name collisions, and to reserve short names
    for recursive parsing.
    """

    def is_kw(param: "Parameter | TypeHint") -> bool:
        # is non-variadic keyword parameter
        if isinstance(param, Parameter):
            return kw_only or param.kind in [
                Parameter.KEYWORD_ONLY,
                Parameter.POSITIONAL_OR_KEYWORD,
            ]
        else:
            return True  # TypeHint is always keyword

    used_names_set = set[str]()
    used_names = list[str]()
    for param_name, param in params:
        if param_name == "help":
            raise ParserConfigError(
                f"Cannot use `help` as parameter name in `{obj_name}`!"
            )

        normalized_annotation = normalize_annotation(param)
        _, _, normalized_annotation = get_naryness(param, normalized_annotation)

        if is_parsable(normalized_annotation):
            name = param_name.replace("_", "-")
            if is_kw(param):
                if name in used_names:
                    raise ParserConfigError(
                        f"Option name `{name}` is used multiple times in `{obj_name}`!"
                        " Recursive parsing requires unique option names among all levels."
                    )
                used_names_set.add(name)
                used_names.append(name)
        elif recurse:
            child_names = collect_param_names(
                _get_params_or_annotations(normalized_annotation),
                obj_name=normalized_annotation.__name__,
                recurse="child",
                kw_only=True,  # children are kw-only for now
            )
            for child_name in child_names:
                if child_name in used_names:
                    raise ParserConfigError(
                        f"Option name `{child_name}` is used multiple times in `{obj_name}`!"
                        " Recursive parsing requires unique option names among all levels."
                    )
                used_names_set.add(child_name)
                used_names.append(child_name)
    return used_names
