import inspect
from dataclasses import MISSING, fields, is_dataclass
from inspect import Parameter
from typing import (
    Any,
    Callable,
    Iterable,
    Literal,
    cast,
    get_args,
    get_origin,
)

from .._docstr import (
    _DocstrParam,
    _DocstrParams,
    _parse_class_docstring,
    _parse_func_docstring,
)
from .._type_utils import (
    _is_typeddict,
    _normalize_type,
    _shorten_type_annotation,
    _strip_annotated,
    _strip_optional,
)
from ..arg import Arg, Name
from ..args import Args
from ..error import ParserConfigError
from ..value_parser import is_parsable
from .parameter import _is_keyword, _is_positional, _is_variadic


def _get_default_factories(cls: type) -> dict[str, Any]:
    """
    Get the default factory functions for all fields in a dataclass.
    """
    if not is_dataclass(cls):
        raise ValueError(f"{cls} is not a dataclass")

    return {
        f.name: f.default_factory
        for f in fields(cls)
        if f.default_factory is not MISSING
    }


def _get_class_initializer_params(cls: type) -> Iterable[tuple[str, Parameter]]:
    """
    Get the parameters of the class's `__init__` method, excluding `self`.
    """
    func = cls.__init__  # type: ignore
    # (mypy thinks cls is an instance)

    # Get the signature of the initializer
    sig = inspect.signature(func)

    # name of the first parameter (usually `self`)
    self_name = next(iter(sig.parameters))

    # filter out the first parameter
    return [
        (name, param) for name, param in sig.parameters.items() if name != self_name
    ]


def _reserve_short_names(
    params: Iterable[tuple[str, Parameter]],
    used_names: list[str],
    arg_helps: _DocstrParams = {},
    used_short_names: set[str] | None = None,
) -> set[str]:
    used_short_names = used_short_names or set()

    # Discover if there are any named options that are of length 1
    # If so, those cannot be used as short names for other options
    for param_name in used_names:
        if len(param_name) == 1:
            used_short_names.add(param_name)

    # Discover if there are any docstring-specified short names,
    # these also take precedence over the first letter of the parameter name
    for param_name, param in params:
        if param.kind in [Parameter.KEYWORD_ONLY, Parameter.POSITIONAL_OR_KEYWORD]:
            if docstr_param := arg_helps.get(param_name):
                if docstr_param.short_name:
                    # if this name is already used, this param cannot use it
                    if docstr_param.short_name in used_short_names:
                        docstr_param.short_name = None
                    else:
                        used_short_names.add(docstr_param.short_name)

    return used_short_names


def _reserve_short_names_typeddict(
    params: Iterable[tuple[str, Any]],
    used_names: list[str],
    arg_helps: _DocstrParams = {},
    used_short_names: set[str] | None = None,
) -> set[str]:
    used_short_names = used_short_names or set()

    # Discover if there are any named options that are of length 1
    # If so, those cannot be used as short names for other options
    for name in used_names:
        if len(name) == 1:
            used_short_names.add(name)

    # Discover if there are any docstring-specified short names,
    # these also take precedence over the first letter of the parameter name
    for name, _ in params:
        if docstr_param := arg_helps.get(name):
            if docstr_param.short_name:
                # if this name is already used, this param cannot use it
                if docstr_param.short_name in used_short_names:
                    docstr_param.short_name = None
                else:
                    used_short_names.add(docstr_param.short_name)

    return used_short_names


def _get_docstr_param(
    param_name: str,
    param: Parameter,
    arg_helps: _DocstrParams,
) -> _DocstrParam:
    param_key: str | None = None
    if param_name in arg_helps:
        param_key = param_name
    elif param.kind is Parameter.VAR_POSITIONAL and f"*{param_name}" in arg_helps:
        # admit both "arg" and "*arg" as valid names
        param_key = f"*{param_name}"
    elif param.kind is Parameter.VAR_KEYWORD and f"**{param_name}" in arg_helps:
        # admit both "arg" and "**arg" as valid names
        param_key = f"**{param_name}"

    return arg_helps[param_key] if param_key else _DocstrParam()


def _get_docstr_key(
    param_name: str,
    arg_helps: _DocstrParams,
) -> _DocstrParam:
    param_key: str | None = None
    if param_name in arg_helps:
        param_key = param_name
    return arg_helps[param_key] if param_key else _DocstrParam()


def _make_name(
    param_name_sub: str,
    named: bool,
    docstr_param: _DocstrParam,
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


def _get_annotation_naryness(
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
        return True, orig, _strip_annotated(args_[0]) if args_ else str
    if orig is tuple and len(args_) == 2 and args_[1] is ...:
        return True, orig, _strip_annotated(args_[0]) if args_ else str
    if normalized_annotation in [list, tuple, set]:
        container_type = cast(type, normalized_annotation)
        return True, container_type, str
    return False, None, normalized_annotation


def _get_naryness(
    param: Parameter, normalized_annotation: Any
) -> tuple[bool, type | None, Any]:
    """
    Get the n-ary status, container type, and normalized annotation for a parameter.
    For n-ary parameters, the type (updated `normalized_annotation`) will refer
    to the inner type.

    If inner type is absent from the hint, assume str.

    Returns:
        `nary`, `container_type`, and `normalized_annotation` as a tuple.
    """
    if param.kind is Parameter.VAR_POSITIONAL:
        return True, list, normalized_annotation

    return _get_annotation_naryness(normalized_annotation)


def _collect_param_names(
    params: Iterable[tuple[str, Parameter]],
    obj_name: str,
    recurse: bool | Literal["child"] = False,
    kw_only: bool = False,
) -> list[str]:
    """
    Get all parameter names in the object hierarchy.
    This is used to detect name collisions, and to reserve short names
    for recursive parsing.
    """
    used_names_set = set()
    used_names = list()
    for param_name, param in params:
        if param_name == "help":
            raise ParserConfigError(
                f"Cannot use `help` as parameter name in `{obj_name}`!"
            )

        normalized_annotation = (
            str
            if param.annotation is Parameter.empty
            else _normalize_type(param.annotation)
        )
        _, _, normalized_annotation = _get_naryness(param, normalized_annotation)

        if is_parsable(normalized_annotation):
            name = param_name.replace("_", "-")
            if (
                param.kind in [Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY]
                or kw_only
            ):
                if name in used_names:
                    raise ParserConfigError(
                        f"Option name `{name}` is used multiple times in `{obj_name}`!"
                        " Recursive parsing requires unique option names among all levels."
                    )
                used_names_set.add(name)
                used_names.append(name)
        elif recurse:
            child_names = _collect_names(
                normalized_annotation,
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


def _collect_keys(
    params: Iterable[tuple[str, Any]],
    obj_name: str,
    recurse: bool | Literal["child"] = False,
    kw_only: bool = False,
) -> list[str]:
    """
    Get all key names in the TypedDict hierarchy.
    This is used to detect name collisions, and to reserve short names
    for recursive parsing.
    """
    used_names_set = set()
    used_names = list()
    for name, annotation in params:
        if name == "help":
            raise ParserConfigError(f"Cannot use `help` as key in `{obj_name}`!")

        normalized_annotation = _normalize_type(annotation)
        _, _, normalized_annotation = _get_annotation_naryness(normalized_annotation)

        if is_parsable(normalized_annotation):
            name = name.replace("_", "-")
            if name in used_names:
                raise ParserConfigError(
                    f"Option name `{name}` is used multiple times in `{obj_name}`!"
                    " Recursive parsing requires unique option names among all levels."
                )
            used_names_set.add(name)
            used_names.append(name)
        elif recurse:
            child_names = _collect_names(
                normalized_annotation,
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


def _collect_names(
    annotation: type,
    obj_name: str,
    recurse: bool | Literal["child"] = False,
    kw_only: bool = False,
) -> list[str]:
    """
    Get all names in the hierarchy of a TypedDict or class.
    This is used to detect name collisions, and to reserve short names
    for recursive parsing.
    """
    if _is_typeddict(annotation):
        return _collect_keys(
            annotation.__annotations__.items(),
            obj_name,
            recurse,
            kw_only,
        )
    else:
        return _collect_param_names(
            _get_class_initializer_params(annotation),
            obj_name,
            recurse,
            kw_only,
        )


def _make_args_from_params(
    params: Iterable[tuple[str, Parameter]],
    obj_name: str,
    brief: str = "",
    arg_helps: _DocstrParams = {},
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

    used_names = _collect_param_names(params, obj_name, recurse, kw_only)
    used_short_names = _used_short_names if _used_short_names is not None else set()
    used_short_names |= _reserve_short_names(
        params, used_names, arg_helps, used_short_names
    )

    # Iterate over the parameters and add arguments based on kind
    for param_name, param in params:
        normalized_annotation = (
            str
            if param.annotation is Parameter.empty
            else _normalize_type(param.annotation)
        )

        required = param.default is inspect.Parameter.empty
        default = param.default if not required else None

        default_factory = default_factories.get(param_name, None)
        docstr_param = _get_docstr_param(param_name, param, arg_helps)

        param_name_sub = param_name.replace("_", "-")

        if recurse == "child" and _is_variadic(param.kind):
            raise ParserConfigError(
                f"Cannot have variadic parameter `{param_name}` in child Args of `{obj_name}`!"
            )

        positional = _is_positional(param.kind) and not kw_only
        named = _is_keyword(param.kind) or kw_only

        nary, container_type, normalized_annotation = _get_naryness(
            param, normalized_annotation
        )

        child_args: Args | None = None
        if is_parsable(normalized_annotation):
            name = _make_name(param_name_sub, named, docstr_param, used_short_names)
        elif recurse:
            if _is_variadic(param.kind):
                raise ParserConfigError(
                    f"Cannot recurse into variadic parameter `{param_name}` "
                    f"in `{obj_name}`!"
                )
            if nary:
                raise ParserConfigError(
                    f"Cannot recurse into n-ary parameter `{param_name}` "
                    f"in `{obj_name}`!"
                )
            normalized_annotation = _strip_optional(normalized_annotation)
            if not isinstance(normalized_annotation, type):
                raise ParserConfigError(
                    f"Cannot recurse into parameter `{param_name}` of non-class type "
                    f"`{_shorten_type_annotation(param.annotation)}` in `{obj_name}`!"
                )
            child_args = make_args_from_class(
                normalized_annotation,
                recurse="child" if recurse else False,
                kw_only=True,  # children are kw-only for now
                _used_short_names=used_short_names,
            )
            child_args._parent = args
            name = Name(long=param_name_sub)
        else:
            raise ParserConfigError(
                f"Unsupported type `{_shorten_type_annotation(param.annotation)}` "
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


def make_args_from_func(
    func: Callable,
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
    brief, arg_helps = _parse_func_docstring(func)

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

    if _is_typeddict(cls):
        return make_args_from_typeddict(
            cls,
            program_name=program_name,
            brief=brief,
            recurse=recurse,
            _used_short_names=_used_short_names,
        )

    params = _get_class_initializer_params(cls)
    arg_helps = _parse_class_docstring(cls)
    default_factories = _get_default_factories(cls) if is_dataclass(cls) else {}

    return _make_args_from_params(
        params,
        cls.__name__,
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
    arg_helps = _parse_class_docstring(td)
    obj_name = td.__name__

    args = Args(brief=brief, program_name=program_name)

    used_names = _collect_keys(params, obj_name, recurse, kw_only=True)
    used_short_names = _used_short_names if _used_short_names is not None else set()
    used_short_names |= _reserve_short_names_typeddict(
        params, used_names, arg_helps, used_short_names
    )

    # Iterate over the parameters and add arguments based on kind
    for param_name, annotation in params:
        normalized_annotation = _normalize_type(annotation)

        required = True  # TODO: handle NotRequired / totality

        docstr_param = _get_docstr_key(param_name, arg_helps)

        param_name_sub = param_name.replace("_", "-")

        positional = False
        named = True

        nary, container_type, normalized_annotation = _get_annotation_naryness(
            normalized_annotation
        )

        child_args: Args | None = None
        if is_parsable(normalized_annotation):
            name = _make_name(param_name_sub, named, docstr_param, used_short_names)
        elif recurse:
            if nary:
                raise ParserConfigError(
                    f"Cannot recurse into n-ary parameter `{param_name}` "
                    f"in `{obj_name}`!"
                )
            normalized_annotation = _strip_optional(normalized_annotation)
            if not isinstance(normalized_annotation, type):
                raise ParserConfigError(
                    f"Cannot recurse into parameter `{param_name}` of non-class type "
                    f"`{_shorten_type_annotation(annotation.annotation)}` in `{obj_name}`!"
                )
            child_args = make_args_from_class(
                normalized_annotation,
                recurse="child" if recurse else False,
                kw_only=True,  # children are kw-only for now
                _used_short_names=used_short_names,
            )
            child_args._parent = args
            name = Name(long=param_name_sub)
        else:
            raise ParserConfigError(
                f"Unsupported type `{_shorten_type_annotation(annotation.annotation)}` "
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
