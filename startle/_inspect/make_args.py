import inspect
from collections.abc import Callable, Sequence
from dataclasses import is_dataclass
from typing import Any, Literal, cast, get_type_hints

from .._docstr import get_param_help, parse_docstring
from .._typing import is_typeddict, shorten_type_annotation, strip_optional
from .._value_parser import is_parsable
from ..arg import Arg, Name
from ..args import Args
from ..error import (
    HelpCollisionError,
    NameCollisionError,
    UnsupportedTypeError,
    VariadicChildParamError,
)
from .classes import get_default_factories, get_initializer_parameters
from .param import Param
from .tree import TreeNode, gather_subtree, leaves


def _check_help_collisions(params: Sequence[Param]) -> None:
    """
    Check for parameters named "help".
    Raises HelpCollisionError if a collision is detected.
    """
    for param in params:
        if param.name == "help":
            raise HelpCollisionError(param.owning_obj_name)


def _check_parsable(params: Sequence[Param]) -> None:
    """
    Check that all parameters have parsable types.
    Raises UnsupportedTypeError if an unparsable type is detected.
    """
    for param in params:
        if not is_parsable(param.normalized_annotation):
            raise UnsupportedTypeError(
                param.name,
                shorten_type_annotation(param.hint),
                param.owning_obj_name,
            )


def _check_name_collisions(params: Sequence[Param], obj_name: str = "") -> None:
    """
    Check for name collisions among parameters.
    Raises NameCollisionError if a collision is detected.
    Only relevant when recursive, and when naming is flat.
    """
    seen_names = set[str]()
    for param in params:
        if param.name in seen_names:
            raise NameCollisionError(param.name, obj_name or param.owning_obj_name)
        seen_names.add(param.name)


def _reserve_short_names(params: Sequence[Param]):
    used_short_names = set[str]()
    short_name_assignments: dict[str, str] = {}

    for param in params:
        if param.is_non_var_keyword:
            name = param.name
            if len(name) == 1:
                assert name not in used_short_names, (
                    f"Duplicate short name {name} in {param.owning_obj_name}"
                )
                used_short_names.add(name)
                short_name_assignments[name] = name

    for param in params:
        if param.is_non_var_keyword:
            custom_short_name = param.help.short_name
            if custom_short_name and custom_short_name not in used_short_names:
                used_short_names.add(custom_short_name)
                short_name_assignments[param.name] = custom_short_name

    return used_short_names, short_name_assignments


def make_arg_from_param(param: Param, name: Name, kw_only: bool = False) -> Arg:
    return Arg(
        name=name,
        type_=param.normalized_annotation,  # type: ignore
        container_type=param.container_type,
        help=param.help.desc,
        required=param.is_required,
        default=param.default,
        default_factory=param.default_factory,
        is_positional=param.is_positional and not kw_only,
        is_named=param.is_keyword or kw_only,
        is_nary=param.is_nary,
    )


def make_args_from_params_flat(
    params: Sequence[Param], brief: str = "", program_name: str = ""
) -> Args:
    args = Args(brief=brief, program_name=program_name)

    _check_help_collisions(params)
    _check_parsable(params)
    used_short_names, short_name_assignments = _reserve_short_names(params)

    for param in params:
        short = short_name_assignments.get(param.name, "")
        if (
            param.is_non_var_keyword
            and not short
            and (first_char := param.name[0]) not in used_short_names
        ):
            used_short_names.add(first_char)
            short_name_assignments[param.name] = first_char
            short = first_char
        arg = make_arg_from_param(
            param=param,
            name=Name(long=param.name.replace("_", "-"), short=short),
        )
        if param.is_var_positional:
            arg.name = Name()
            args.enable_unknown_args(arg)
        elif param.is_var_keyword:
            arg.name = Name(long="<key>")
            args.enable_unknown_opts(arg)
        else:
            args.add(arg)

    return args


def make_args_from_params_recursive(
    params: Sequence[Param],
    brief: str = "",
    program_name: str = "",
    naming: Literal["nested", "flat"] = "flat",
) -> Args:
    args = Args(brief=brief, program_name=program_name)

    forest = [gather_subtree(param) for param in params]
    leaf_params = list(leaves(forest))

    _check_help_collisions(leaf_params)
    _check_parsable(leaf_params)
    # Use the first param's owning_obj_name as the top-level obj name
    obj_name = params[0].owning_obj_name if params else ""

    if naming == "nested":
        used_short_names, short_name_assignments = _reserve_short_names(params)
    else:
        _check_name_collisions(leaf_params, obj_name=obj_name)
        used_short_names, short_name_assignments = _reserve_short_names(leaf_params)

    def traverse(node: TreeNode[Param], args: Args, parent_name: str = ""):
        kw_only = node.parent is not None  # children are kw-only
        is_nested_child = naming == "nested" and kw_only

        if not node.children:
            assert is_parsable(node.data.normalized_annotation)
            param = node.data

            # Variadic params are not allowed in child Args
            if kw_only and (param.is_var_positional or param.is_var_keyword):
                raise VariadicChildParamError(param.name, param.owning_obj_name)

            if is_nested_child:
                # In nested naming, child leaves don't get short names
                param_name_sub = f"{parent_name}.{param.name}".replace("_", "-")
                name = Name(long=param_name_sub)
            else:
                short = short_name_assignments.get(param.name, "")
                if (
                    param.is_non_var_keyword
                    and not short
                    and (first_char := param.name[0]) not in used_short_names
                ):
                    used_short_names.add(first_char)
                    short_name_assignments[param.name] = first_char
                    short = first_char
                name = Name(long=param.name.replace("_", "-"), short=short)

            arg = make_arg_from_param(
                param=param,
                name=name,
                kw_only=kw_only,
            )
            if param.is_var_positional:
                arg.name = Name()
                args.enable_unknown_args(arg)
            elif param.is_var_keyword:
                arg.name = Name(long="<key>")
                args.enable_unknown_opts(arg)
            else:
                args.add(arg)
        else:
            child_args = Args()
            child_parent_name = (
                f"{parent_name}.{node.data.name}" if parent_name else node.data.name
            )
            for child in node.children:
                traverse(child, child_args, parent_name=child_parent_name)

            # We add a positional variadic argument for convenience when parsing
            # recursively. Child Args will consume its own arguments and leave
            # the rest for the parent to handle.
            if node.parent is not None:  # only add to non-root nodes
                child_args.enable_unknown_args(
                    Arg(
                        name=Name(),
                        type_=str,
                        is_positional=True,
                        is_nary=True,
                        container_type=list,
                        help="Additional arguments for the parent parser.",
                    )
                )

            child_args._parent = args  # type: ignore

            actual_type = strip_optional(node.data.normalized_annotation)
            node_name = (
                node.data.name
                if naming == "flat"
                else (
                    f"{parent_name}.{node.data.name}" if parent_name else node.data.name
                )
            )
            arg = Arg(
                name=Name(long=node_name.replace("_", "-")),
                type_=actual_type,  # type: ignore
                container_type=node.data.container_type,
                help=node.data.help.desc,
                required=node.data.is_required,
                default=node.data.default,
                default_factory=node.data.default_factory,
                is_positional=node.data.is_positional and not kw_only,
                is_named=node.data.is_keyword or kw_only,
                is_nary=node.data.is_nary,
                args=child_args,
            )
            args.add(arg)

    for node in forest:
        traverse(node, args)

    return args


def make_params_from_func(func: Callable[..., Any]) -> tuple[list[Param], str]:
    sig = inspect.signature(func)
    params = sig.parameters.items()
    hints = get_type_hints(func, include_extras=True)

    # Attempt to parse brief and arg descriptions from docstring
    brief, arg_helps = parse_docstring(func)

    return [
        Param.from_parameter(
            parameter=param,
            hint=hints.get(param_name, str),
            help=get_param_help(param, arg_helps),
            owning_obj_name=f"{func.__name__}()",
        )
        for param_name, param in params
    ], brief


def make_args_from_func(
    func: Callable[..., Any],
    program_name: str = "",
    recurse: bool = False,
    naming: Literal["nested", "flat"] = "flat",
) -> Args:
    """
    Create an Args object from a function signature.

    Args:
        func: The function to create Args from.
        program_name: The name of the program, for help string.
        recurse: Whether to recurse into nested Args.
        naming: The naming strategy for nested Args.
    """

    if not recurse:
        params, brief = make_params_from_func(func)
        return make_args_from_params_flat(
            params=params,
            brief=brief,
            program_name=program_name,
        )
    else:
        params, brief = make_params_from_func(func)
        return make_args_from_params_recursive(
            params=params,
            brief=brief,
            program_name=program_name,
            naming=naming,
        )


def make_params_from_class(cls: type) -> list[Param]:
    params = get_initializer_parameters(cls)
    hints = get_type_hints(cls.__init__, include_extras=True)
    _, arg_helps = parse_docstring(cls)
    default_factories = get_default_factories(cls) if is_dataclass(cls) else {}

    return [
        Param.from_parameter(
            parameter=param,
            hint=hints.get(param.name, str),
            help=get_param_help(param, arg_helps),
            owning_obj_name=f"{cls.__name__}",  # type: ignore
            default_factory=default_factories.get(param.name, None),
        )
        for _, param in params
    ]


def make_params_from_td(cls: type) -> list[Param]:
    params = get_type_hints(cls, include_extras=True).items()
    optional_keys = cast(frozenset[str], cls.__optional_keys__)  # type: ignore
    required_keys = cast(frozenset[str], cls.__required_keys__)  # type: ignore
    _, arg_helps = parse_docstring(cls)

    return [
        Param.from_td_param(
            param_name=param_name,
            annotation=annotation,
            help=arg_helps.get(param_name),
            in_required_keys=param_name in required_keys,
            in_optional_keys=param_name in optional_keys,
            owning_obj_name=f"{cls.__name__}",
        )
        for param_name, annotation in params
    ]


def make_args_from_class(
    cls: type,
    *,
    program_name: str = "",
    brief: str = "",
    recurse: bool = False,
    naming: Literal["nested", "flat"] = "flat",
) -> Args:
    """
    Create an Args object from a class's `__init__` signature and docstring.

    Args:
        cls: The class to create Args from.
        program_name: The name of the program, for help string.
        brief: A brief description of the class, for help string.
        recurse: Whether to recurse into nested Args.
        naming: The naming strategy for nested Args.
    """
    # TODO: check if cls is a class?

    if is_typeddict(cls):
        params = make_params_from_td(cls)
    else:
        params = make_params_from_class(cls)

    if not recurse:
        return make_args_from_params_flat(
            params=params,
            brief=brief,
            program_name=program_name,
        )
    else:
        return make_args_from_params_recursive(
            params=params,
            brief=brief,
            program_name=program_name,
            naming=naming,
        )
