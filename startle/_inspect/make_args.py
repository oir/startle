import inspect
from collections.abc import Callable, Iterable, Mapping
from dataclasses import is_dataclass
from inspect import Parameter
from typing import Any, cast, get_type_hints

from .._docstr import ParamHelp, ParamHelps, get_param_help, parse_docstring
from .._type_utils import (
    TypeHint,
    is_typeddict,
    normalize_annotation,
    shorten_type_annotation,
    strip_optional,
)
from .._value_parser import is_parsable
from ..arg import Arg, Name
from ..args import Args
from ..error import UnsupportedTypeError, VariadicChildParamError
from .classes import get_class_initializer_params
from .config import CommonConfig
from .dataclasses import get_default_factories
from .names import (
    collect_param_names,
    get_naryness,
    make_name,
    reserve_short_names,
)
from .parameter import is_keyword, is_positional, is_variadic
from .recursable import check_recursable
from .typeddict import make_args_from_td


def _make_arg_from_param(
    *,
    param: Parameter,
    hint: TypeHint,
    help: ParamHelp,
    default_factory: Any,
    used_short_names: set[str],
    args: Args,
    cfg: CommonConfig,
) -> Arg:
    param_name = param.name
    normalized_annotation = normalize_annotation(hint)

    required = param.default is inspect.Parameter.empty
    default = param.default if not required else None

    if cfg.recurse == "child" and cfg.naming == "nested":
        param_name_sub = f"{cfg.parent_name}.{param_name}".replace("_", "-")
    else:
        param_name_sub = param_name.replace("_", "-")

    if cfg.recurse == "child" and is_variadic(param):
        raise VariadicChildParamError(param_name, cfg.obj_name)

    positional = is_positional(param) and not cfg.kw_only
    named = is_keyword(param) or cfg.kw_only

    nary, container_type, normalized_annotation = get_naryness(
        param, normalized_annotation
    )

    child_args: Args | None = None
    if is_parsable(normalized_annotation):
        if cfg.recurse == "child" and cfg.naming == "nested":
            name = Name(long=param_name_sub)
        else:
            name = make_name(param_name_sub, named, help, used_short_names)
    elif cfg.recurse:
        check_recursable(param_name, param, normalized_annotation, cfg.obj_name, nary)
        normalized_annotation = strip_optional(normalized_annotation)
        assert isinstance(normalized_annotation, type), (
            "Unexpected type form that is not a type!"
        )

        child_args = make_args_from_class(
            normalized_annotation,
            used_short_names=used_short_names,
            cfg=CommonConfig(
                recurse="child" if cfg.recurse else False,
                naming=cfg.naming,
                kw_only=True,  # children are kw-only for now
                parent_name=f"{cfg.parent_name}.{param_name}"
                if cfg.recurse == "child"
                else param_name,
            ),
        )
        child_args._parent = args  # type: ignore
        name = Name(long=param_name_sub)
    else:
        raise UnsupportedTypeError(
            param_name, shorten_type_annotation(param.annotation), cfg.obj_name
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
        default=default,
        default_factory=default_factory,
        is_positional=positional,
        is_named=named,
        is_nary=nary,
        args=child_args,
    )


def _make_args_from_params(
    *,
    params: Iterable[tuple[str, Parameter]],
    hints: Mapping[str, TypeHint],
    brief: str = "",
    helps: ParamHelps | None = None,
    program_name: str = "",
    default_factories: dict[str, Any] | None = None,
    used_short_names: set[str] | None = None,
    cfg: CommonConfig,
) -> Args:
    """
    Create an Args object from a list of parameters.

    Args:
        params: An iterable of (parameter name, Parameter) tuples.
        brief: A brief description of the object, for help string.
        helps: A mapping from parameter names to their docstring descriptions.
        program_name: The name of the program, for help string.
        default_factories: A mapping from parameter names to their default factory functions.
        used_short_names: Set of already used short names coming from parent Args.
            Modified in-place if not None.
        cfg: Configuration.
    """
    args = Args(brief=brief, program_name=program_name)

    helps = helps or {}
    default_factories = default_factories or {}

    used_names = collect_param_names(params, hints, cfg)
    used_short_names = used_short_names if used_short_names is not None else set[str]()
    used_short_names |= reserve_short_names(params, used_names, helps, used_short_names)

    # Iterate over the parameters and add arguments based on kind
    for param_name, param in params:
        arg = _make_arg_from_param(
            param=param,
            hint=hints.get(param_name, str),
            help=get_param_help(param_name, param, helps),
            default_factory=default_factories.get(param_name, None),
            used_short_names=used_short_names,
            args=args,
            cfg=cfg,
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


def make_args_from_func(
    func: Callable[..., Any],
    program_name: str = "",
    cfg: CommonConfig | None = None,
) -> Args:
    """
    Create an Args object from a function signature.

    Args:
        func: The function to create Args from.
        program_name: The name of the program, for help string.
        cfg: Configuration.
    """
    # Get the signature of the function
    sig = inspect.signature(func)
    params = sig.parameters.items()
    hints = get_type_hints(func, include_extras=True)

    # Attempt to parse brief and arg descriptions from docstring
    brief, arg_helps = parse_docstring(func)
    cfg = cfg or CommonConfig()

    return _make_args_from_params(
        params=params,
        hints=hints,
        brief=brief,
        helps=arg_helps,
        program_name=program_name,
        cfg=cfg.copy(obj_name=f"{func.__name__}()"),
    )


def make_args_from_class(
    cls: type,
    *,
    program_name: str = "",
    brief: str = "",
    used_short_names: set[str] | None = None,
    cfg: CommonConfig | None = None,
) -> Args:
    """
    Create an Args object from a class's `__init__` signature and docstring.

    Args:
        cls: The class to create Args from.
        program_name: The name of the program, for help string.
        brief: A brief description of the class, for help string.
        used_short_names: Set of already used short names coming from parent Args.
            Modified in-place if not None.
        cfg: Configuration.
    """
    # TODO: check if cls is a class?

    cfg = cfg or CommonConfig()

    if is_typeddict(cls):
        return make_args_from_td(
            cls,
            program_name=program_name,
            brief=brief,
            used_short_names=used_short_names,
            cfg=cfg,
        )

    params = get_class_initializer_params(cls)
    hints = get_type_hints(cls.__init__, include_extras=True)
    _, arg_helps = parse_docstring(cls)
    default_factories = get_default_factories(cls) if is_dataclass(cls) else {}

    return _make_args_from_params(
        params=params,
        hints=hints,
        brief=brief,
        helps=arg_helps,
        program_name=program_name,
        default_factories=default_factories,
        used_short_names=used_short_names,
        cfg=cfg.copy(obj_name=f"{cls.__name__}"),  # type: ignore
    )
