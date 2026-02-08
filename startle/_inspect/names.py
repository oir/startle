from collections.abc import Iterable, Mapping
from inspect import Parameter

from .._docstr import ParamHelp, ParamHelps
from .._type_utils import TypeHint, is_typeddict, normalize_annotation
from .._value_parser import is_parsable
from ..arg import Name
from ..error import HelpCollisionError, NameCollisionError
from .classes import get_class_initializer_params
from .config import CommonConfig
from .nary import get_naryness


def reserve_short_names(
    params: Iterable[tuple[str, "Parameter | TypeHint"]],
    used_names: list[str],
    arg_helps: ParamHelps | None = None,
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

    arg_helps = arg_helps or {}

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
            # TODO: check for docstring-specified short name conflicts
            return Name(short=docstr_param.short_name, long=param_name_sub)
        if param_name_sub[0] not in used_short_names:
            used_short_names.add(param_name_sub[0])
            return Name(short=param_name_sub[0], long=param_name_sub)
    return Name(long=param_name_sub)


def _get_params_or_annotations(
    annotation: type,
) -> Iterable[tuple[str, "Parameter | TypeHint"]]:
    if is_typeddict(annotation):
        return annotation.__annotations__.items()
    else:
        return get_class_initializer_params(annotation)


def _get_hints(
    annotation: type,
) -> Mapping[str, TypeHint]:
    if is_typeddict(annotation):
        return annotation.__annotations__
    else:
        from typing import get_type_hints

        return get_type_hints(annotation.__init__, include_extras=True)


def collect_param_names(
    params: Iterable[tuple[str, "Parameter | TypeHint"]],
    hints: Mapping[str, TypeHint],
    cfg: CommonConfig,
) -> list[str]:
    """
    Get all parameter names in the object hierarchy.
    This is used to detect name collisions, and to reserve short names
    for recursive parsing.
    """

    def is_kw(param: "Parameter | TypeHint") -> bool:
        # is non-variadic keyword parameter
        if isinstance(param, Parameter):
            return cfg.kw_only or param.kind in [
                Parameter.KEYWORD_ONLY,
                Parameter.POSITIONAL_OR_KEYWORD,
            ]
        else:
            return True  # TypeHint is always keyword

    used_names_set = set[str]()
    used_names = list[str]()
    for param_name, param in params:
        if param_name == "help":
            raise HelpCollisionError(cfg.obj_name)

        normalized_annotation = normalize_annotation(hints.get(param_name, str))
        _, _, normalized_annotation = get_naryness(param, normalized_annotation)

        if is_parsable(normalized_annotation):
            if cfg.recurse == "child" and cfg.naming == "nested":
                name = f"{cfg.parent_name}.{param_name}".replace("_", "-")
            else:
                name = param_name.replace("_", "-")
            if is_kw(param):
                if name in used_names:
                    raise NameCollisionError(name, cfg.obj_name)
                used_names_set.add(name)
                used_names.append(name)
        elif cfg.recurse:
            child_names = collect_param_names(
                params=_get_params_or_annotations(normalized_annotation),
                hints=_get_hints(normalized_annotation),
                cfg=CommonConfig(
                    obj_name=normalized_annotation.__name__,
                    recurse="child",
                    naming=cfg.naming,
                    kw_only=True,  # children are kw-only for now
                    parent_name=f"{cfg.parent_name}.{param_name}",
                ),
            )
            for child_name in child_names:
                if child_name in used_names:
                    raise NameCollisionError(child_name, cfg.obj_name)
                used_names_set.add(child_name)
                used_names.append(child_name)
    return used_names
