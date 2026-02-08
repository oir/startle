from typing import cast, get_type_hints

from .._docstr import ParamHelp, get_param_help, parse_docstring
from .._type_utils import (
    normalize_annotation,
    shorten_type_annotation,
    strip_not_required,
    strip_optional,
    strip_required,
)
from .._value_parser import is_parsable
from ..arg import Arg, Name
from ..args import Args, Missing
from ..error import (
    NaryNonRecursableParamError,
    NonClassNonRecursableParamError,
    UnsupportedTypeError,
)
from .config import CommonConfig
from .names import collect_param_names, make_name, reserve_short_names
from .nary import get_annotation_naryness


def _make_arg_from_td_param(
    *,
    param_name: str,
    annotation: type,
    cfg: CommonConfig,
    help: ParamHelp,
    used_short_names: set[str],
    required_keys: frozenset[str],
    optional_keys: frozenset[str],
    args: Args,
) -> Arg:
    from .make_args import make_args_from_class

    is_required, normalized_annotation = strip_required(annotation)
    is_not_required, normalized_annotation = strip_not_required(normalized_annotation)
    normalized_annotation = normalize_annotation(normalized_annotation)

    required = param_name in required_keys or param_name not in optional_keys
    # NotRequired[] and Required[] are stronger than total=False/True
    if is_required:
        required = True
    elif is_not_required:
        required = False

    param_name_sub = param_name.replace("_", "-")

    positional = False
    named = True

    nary, container_type, normalized_annotation = get_annotation_naryness(
        normalized_annotation
    )

    child_args: Args | None = None
    if is_parsable(normalized_annotation):
        if cfg.recurse == "child" and cfg.naming == "nested":
            name = Name(long=f"{cfg.parent_name}.{param_name_sub}")
        else:
            name = make_name(param_name_sub, named, help, used_short_names)
    elif cfg.recurse:
        if nary:
            raise NaryNonRecursableParamError(param_name, cfg.obj_name)
        normalized_annotation = strip_optional(normalized_annotation)
        if not isinstance(normalized_annotation, type):
            raise NonClassNonRecursableParamError(
                param_name, shorten_type_annotation(annotation), cfg.obj_name
            )
        child_args = make_args_from_class(
            normalized_annotation,
            used_short_names=used_short_names,
            cfg=CommonConfig(
                recurse="child" if cfg.recurse else False,
                naming=cfg.naming,
                kw_only=True,  # children are kw-only for now
                parent_name=f"{cfg.parent_name}.{param_name}",
            ),
        )
        child_args._parent = args  # type: ignore
        name = Name(
            long=f"{cfg.parent_name}.{param_name_sub}"
            if cfg.naming == "nested"
            else param_name_sub
        )
    else:
        raise UnsupportedTypeError(
            param_name, shorten_type_annotation(annotation), cfg.obj_name
        )

    # the following should hold if normalized_annotation is parsable
    # TODO: double check below for Optional[...]
    normalized_annotation = cast(type, normalized_annotation)

    return Arg(
        name=name,
        type_=normalized_annotation,
        container_type=container_type,
        help=help.desc,
        required=required,
        default=Missing if not required else None,
        default_factory=None,
        is_positional=positional,
        is_named=named,
        is_nary=nary,
        args=child_args,
    )


def make_args_from_td(
    td: type,
    *,
    program_name: str = "",
    brief: str = "",
    used_short_names: set[str] | None = None,
    cfg: CommonConfig,
) -> Args:
    """
    Create an Args object from a TypedDict.

    Args:
        td: The TypedDict to create Args from.
        program_name: The name of the program, for help string.
        brief: A brief description of the TypedDict, for help string.
        used_short_names: Set of already used short names coming from parent Args.
            Modified in-place if not None.
        cfg: Configuration.
    """

    params = get_type_hints(td, include_extras=True).items()
    hints = get_type_hints(td, include_extras=True)
    optional_keys = cast(frozenset[str], td.__optional_keys__)  # type: ignore
    required_keys = cast(frozenset[str], td.__required_keys__)  # type: ignore
    _, arg_helps = parse_docstring(td)
    obj_name = td.__name__

    args = Args(brief=brief, program_name=program_name)
    cfg = cfg | dict(obj_name=obj_name, kw_only=True)  # type: ignore

    used_names = collect_param_names(params, hints, cfg)
    used_short_names = used_short_names if used_short_names is not None else set[str]()
    used_short_names |= reserve_short_names(
        params, used_names, arg_helps, used_short_names
    )

    # Iterate over the parameters and add arguments based on kind
    for param_name, annotation in params:
        arg = _make_arg_from_td_param(
            param_name=param_name,
            annotation=annotation,
            help=get_param_help(param_name, annotation, arg_helps),
            used_short_names=used_short_names,
            required_keys=required_keys,
            optional_keys=optional_keys,
            args=args,
            cfg=cfg,
        )
        args.add(arg)

    # We add a positional variadic argument for convenience when parsing
    # recursively. Child Args will consume its own arguments and leave
    # the rest for the parent to handle.
    if cfg.recurse == "child":
        args.enable_unknown_args(
            Arg(
                name=Name(),
                type_=str,
                is_positional=True,
                is_nary=True,
                container_type=list,
                help="Additional arguments for the parent parser.",
            )
        )
    return args
