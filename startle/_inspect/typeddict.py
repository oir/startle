from typing import (
    Literal,
    cast,
    get_type_hints,
)

from .._docstr import parse_docstring
from .._type_utils import (
    normalize_type,
    shorten_type_annotation,
    strip_not_required,
    strip_optional,
    strip_required,
)
from .._value_parser import is_parsable
from ..arg import Arg, Name
from ..args import Args, Missing
from ..error import ParserConfigError
from .names import (
    collect_param_names,
    get_annotation_naryness,
    make_name,
    reserve_short_names,
)


def make_args_from_typeddict(
    td: type,
    *,
    program_name: str = "",
    brief: str = "",
    recurse: bool | Literal["child"] = False,
    _used_short_names: set[str] | None = None,
) -> Args:
    """
    Create an Args object from a TypedDict.

    Args:
        td: The TypedDict to create Args from.
        program_name: The name of the program, for help string.
        brief: A brief description of the TypedDict, for help string.
        recurse: Whether to recurse into non-parsable types to create sub-Args.
            "child" is same as True, but it also indicates that this is not the root Args.
        _used_short_names: (internal) set of already used short names coming from parent Args.
            Modified in-place if not None.
    """
    from .make_args import get_param_help, make_args_from_class

    params = get_type_hints(td, include_extras=True).items()
    optional_keys: frozenset[str] = td.__optional_keys__  # type: ignore
    required_keys: frozenset[str] = td.__required_keys__  # type: ignore
    _, arg_helps = parse_docstring(td)
    obj_name = td.__name__

    args = Args(brief=brief, program_name=program_name)

    used_names = collect_param_names(params, obj_name, recurse, kw_only=True)
    used_short_names = (
        _used_short_names if _used_short_names is not None else set[str]()
    )
    used_short_names |= reserve_short_names(
        params, used_names, arg_helps, used_short_names
    )

    # Iterate over the parameters and add arguments based on kind
    for param_name, annotation in params:
        is_required, normalized_annotation = strip_required(annotation)
        is_not_required, normalized_annotation = strip_not_required(
            normalized_annotation
        )
        normalized_annotation = normalize_type(normalized_annotation)

        required = param_name in required_keys or param_name not in optional_keys
        # NotRequired[] and Required[] are stronger than total=False/True
        if is_required:
            required = True
        elif is_not_required:
            required = False

        docstr_param = get_param_help(param_name, annotation, arg_helps)

        param_name_sub = param_name.replace("_", "-")

        positional = False
        named = True

        nary, container_type, normalized_annotation = get_annotation_naryness(
            normalized_annotation
        )

        child_args: Args | None = None
        if is_parsable(normalized_annotation):
            name = make_name(param_name_sub, named, docstr_param, used_short_names)
        elif recurse:
            if nary:
                raise ParserConfigError(
                    f"Cannot recurse into n-ary parameter `{param_name}` "
                    f"in `{obj_name}`!"
                )
            normalized_annotation = strip_optional(normalized_annotation)
            if not isinstance(normalized_annotation, type):
                raise ParserConfigError(
                    f"Cannot recurse into parameter `{param_name}` of non-class type "
                    f"`{shorten_type_annotation(annotation)}` in `{obj_name}`!"
                )
            child_args = make_args_from_class(
                normalized_annotation,
                recurse="child" if recurse else False,
                kw_only=True,  # children are kw-only for now
                _used_short_names=used_short_names,
            )
            child_args._parent = args  # type: ignore
            name = Name(long=param_name_sub)
        else:
            raise ParserConfigError(
                f"Unsupported type `{shorten_type_annotation(annotation)}` "
                f"for parameter `{param_name}` in `{obj_name}`!"
            )

        # the following should hold if normalized_annotation is parsable
        # TODO: double check below for Optional[...]
        normalized_annotation = cast(type, normalized_annotation)

        arg = Arg(
            name=name,
            type_=normalized_annotation,
            container_type=container_type,
            help=docstr_param.desc,
            required=required,
            default=Missing if not required else None,
            default_factory=None,
            is_positional=positional,
            is_named=named,
            is_nary=nary,
            args=child_args,
        )
        args.add(arg)

    # We add a positional variadic argument for convenience when parsing
    # recursively. Child Args will consume its own arguments and leave
    # the rest for the parent to handle.
    if recurse == "child":
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
