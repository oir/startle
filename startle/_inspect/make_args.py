import inspect
from dataclasses import is_dataclass
from inspect import Parameter
from typing import (
    Any,
    Callable,
    Iterable,
    Literal,
    ParamSpec,
    cast,
)

from .._docstr import ParamHelp, ParamHelps, parse_docstring
from .._type_utils import (
    TypeHint,
    is_typeddict,
    normalize_annotation,
    normalize_type,
    shorten_type_annotation,
    strip_optional,
)
from ..arg import Arg, Name
from ..args import Args
from ..error import ParserConfigError
from ..value_parser import is_parsable
from .classes import get_class_initializer_params
from .dataclasses import get_default_factories
from .names import (
    collect_param_names,
    get_annotation_naryness,
    get_naryness,
    make_name,
    reserve_short_names,
)
from .parameter import is_keyword, is_positional, is_variadic


def get_param_help(
    param_name: str,
    param: Parameter | TypeHint,
    arg_helps: ParamHelps,
) -> ParamHelp:
    param_key: str | None = None
    if param_name in arg_helps:
        param_key = param_name
    elif isinstance(param, Parameter):
        if param.kind is Parameter.VAR_POSITIONAL and f"*{param_name}" in arg_helps:
            # admit both "arg" and "*arg" as valid names
            param_key = f"*{param_name}"
        elif param.kind is Parameter.VAR_KEYWORD and f"**{param_name}" in arg_helps:
            # admit both "arg" and "**arg" as valid names
            param_key = f"**{param_name}"

    return arg_helps[param_key] if param_key else ParamHelp()


def check_recursable(
    param_name: str,
    param: Parameter,
    normalized_annotation: Any,
    obj_name: str,
    nary: bool,
) -> None:
    """
    Raise if the given parameter cannot be recursed into, no-op otherwise.
    """
    if is_variadic(param):
        raise ParserConfigError(
            f"Cannot recurse into variadic parameter `{param_name}` in `{obj_name}`!"
        )
    if nary:
        raise ParserConfigError(
            f"Cannot recurse into n-ary parameter `{param_name}` in `{obj_name}`!"
        )
    normalized_annotation = strip_optional(normalized_annotation)
    if not isinstance(normalized_annotation, type):
        raise ParserConfigError(
            f"Cannot recurse into parameter `{param_name}` of non-class type "
            f"`{shorten_type_annotation(param.annotation)}` in `{obj_name}`!"
        )


def _make_args_from_params(
    params: Iterable[tuple[str, Parameter]],
    obj_name: str,
    brief: str = "",
    arg_helps: ParamHelps = {},
    program_name: str = "",
    default_factories: dict[str, Any] = {},
    recurse: bool | Literal["child"] = False,
    kw_only: bool = False,
    _used_short_names: set[str] | None = None,
) -> Args:
    """
    Create an Args object from a list of parameters.

    Args:
        params: An iterable of (parameter name, Parameter) tuples.
        obj_name: Name of the object (function or class) these parameters belong to.
        brief: A brief description of the object, for help string.
        arg_helps: A mapping from parameter names to their docstring descriptions.
        program_name: The name of the program, for help string.
        default_factories: A mapping from parameter names to their default factory functions.
        recurse: Whether to recurse into non-parsable types to create sub-Args.
            "child" is same as True, but it also indicates that this is not the root Args.
        kw_only: If true, make all parameters keyword-only, regardless of their definition.
        _used_short_names: (internal) set of already used short names coming from parent Args.
            Modified in-place if not None.
    """
    args = Args(brief=brief, program_name=program_name)

    used_names = collect_param_names(params, obj_name, recurse, kw_only)
    used_short_names = (
        _used_short_names if _used_short_names is not None else set[str]()
    )
    used_short_names |= reserve_short_names(
        params, used_names, arg_helps, used_short_names
    )

    # Iterate over the parameters and add arguments based on kind
    for param_name, param in params:
        normalized_annotation = normalize_annotation(param)

        required = param.default is inspect.Parameter.empty
        default = param.default if not required else None

        default_factory = default_factories.get(param_name, None)
        docstr_param = get_param_help(param_name, param, arg_helps)

        param_name_sub = param_name.replace("_", "-")

        if recurse == "child" and is_variadic(param):
            raise ParserConfigError(
                f"Cannot have variadic parameter `{param_name}` in child Args of `{obj_name}`!"
            )

        positional = is_positional(param) and not kw_only
        named = is_keyword(param) or kw_only

        nary, container_type, normalized_annotation = get_naryness(
            param, normalized_annotation
        )

        child_args: Args | None = None
        if is_parsable(normalized_annotation):
            name = make_name(param_name_sub, named, docstr_param, used_short_names)
        elif recurse:
            check_recursable(param_name, param, normalized_annotation, obj_name, nary)
            normalized_annotation = strip_optional(normalized_annotation)
            assert isinstance(normalized_annotation, type), (
                "Unexpected type form that is not a type!"
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
                f"Unsupported type `{shorten_type_annotation(param.annotation)}` "
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
            default=default,
            default_factory=default_factory,
            is_positional=positional,
            is_named=named,
            is_nary=nary,
            args=child_args,
        )
        if param.kind is Parameter.VAR_POSITIONAL:
            arg.name = Name()
            args.enable_unknown_args(arg)
        elif param.kind is Parameter.VAR_KEYWORD:
            arg.name = Name(long="<key>")
            args.enable_unknown_opts(arg)
        else:
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


P = ParamSpec("P")


def make_args_from_func(
    func: Callable[P, Any],
    *,
    program_name: str = "",
    recurse: bool | Literal["child"] = False,
    kw_only: bool = False,
) -> Args:
    """
    Create an Args object from a function signature.

    Args:
        func: The function to create Args from.
        program_name: The name of the program, for help string.
        recurse: Whether to recurse into non-parsable types to create sub-Args.
            "child" is same as True, but it also indicates that this is not the root Args.
        kw_only: If true, make all parameters keyword-only, regardless of their definition.
    """
    # Get the signature of the function
    sig = inspect.signature(func)
    params = sig.parameters.items()

    # Attempt to parse brief and arg descriptions from docstring
    brief, arg_helps = parse_docstring(func)

    return _make_args_from_params(
        params,
        f"{func.__name__}()",
        brief,
        arg_helps,
        program_name,
        recurse=recurse,
        kw_only=kw_only,
    )


def make_args_from_class(
    cls: type,
    *,
    program_name: str = "",
    brief: str = "",
    recurse: bool | Literal["child"] = False,
    kw_only: bool = False,
    _used_short_names: set[str] | None = None,
) -> Args:
    """
    Create an Args object from a class's `__init__` signature and docstring.

    Args:
        cls: The class to create Args from.
        program_name: The name of the program, for help string.
        brief: A brief description of the class, for help string.
        recurse: Whether to recurse into non-parsable types to create sub-Args.
            "child" is same as True, but it also indicates that this is not the root Args.
        kw_only: If true, make all parameters keyword-only, regardless of their definition.
        _used_short_names: (internal) set of already used short names coming from parent Args.
            Modified in-place if not None.
    """
    # TODO: check if cls is a class?

    if is_typeddict(cls):
        return make_args_from_typeddict(
            cls,
            program_name=program_name,
            brief=brief,
            recurse=recurse,
            _used_short_names=_used_short_names,
        )

    params = get_class_initializer_params(cls)
    _, arg_helps = parse_docstring(cls)
    default_factories = get_default_factories(cls) if is_dataclass(cls) else {}

    return _make_args_from_params(
        params,
        cls.__name__,  # type: ignore
        brief,
        arg_helps,
        program_name,
        default_factories,
        recurse,
        kw_only,
        _used_short_names,
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
    params = td.__annotations__.items()
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
        normalized_annotation = normalize_type(annotation)

        required = True  # TODO: handle NotRequired / totality

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
                    f"`{shorten_type_annotation(annotation.annotation)}` in `{obj_name}`!"
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
                f"Unsupported type `{shorten_type_annotation(annotation.annotation)}` "
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
            default=None,
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
