"""
Utilities for recursive inspection when parsing nested structures.
"""

from collections.abc import Iterable
from dataclasses import dataclass, is_dataclass
from typing import Generic, TypeVar, cast, get_type_hints

from .._docstr import ParamHelp, parse_docstring
from .._typing import is_typeddict, shorten, strip_optional
from .._value_parser import is_parsable
from ..error import RecursiveTypeError
from .classes import get_default_factories, get_initializer_parameters
from .param import Param

T = TypeVar("T")


@dataclass(kw_only=True)
class TreeNode(Generic[T]):
    data: T
    children: list["TreeNode[T]"]
    parent: "TreeNode[T] | None" = None


def gather_children(param: Param) -> list[Param]:
    """
    Collect immediate children of a parameter (non-recursively).
    """

    if is_parsable(param.normalized_hint):
        # If parsable, we consider this a leaf node.
        return []

    param.check_recursable()

    cls = strip_optional(param.normalized_hint)

    children: list[Param] = []
    if is_typeddict(cls):
        parameters = get_type_hints(cls, include_extras=True).items()
        optional_keys = cast(frozenset[str], cls.__optional_keys__)  # type: ignore
        required_keys = cast(frozenset[str], cls.__required_keys__)  # type: ignore
        _, arg_helps = parse_docstring(cls)

        for param_name, annotation in parameters:
            child_info = Param.from_td_param(
                param_name=param_name,
                annotation=annotation,
                help=arg_helps.get(param_name, ParamHelp()),
                in_required_keys=param_name in required_keys,
                in_optional_keys=param_name in optional_keys,
                owning_obj_name=cls.__name__,
            )
            children.append(child_info)
    else:
        # regular class
        assert isinstance(cls, type), "Unexpected type form that is not a type!"

        parameters = get_initializer_parameters(cls)
        hints = get_type_hints(cls.__init__, include_extras=True)
        _, arg_helps = parse_docstring(cls)
        default_factories = get_default_factories(cls) if is_dataclass(cls) else {}

        # odd pyright quirk, have to repeat this assert
        assert isinstance(cls, type), "Unexpected type form that is not a type!"

        for _, parameter in parameters:
            child_info = Param.from_parameter(
                parameter=parameter,
                hint=hints.get(parameter.name, str),
                help=arg_helps.get(parameter.name),
                default_factory=default_factories.get(parameter.name, None),
                owning_obj_name=cls.__name__,
            )
            children.append(child_info)

    return children


def gather_subtree(
    param: Param, ancestors: tuple[type, ...] = ()
) -> TreeNode[Param]:
    """
    Collect the entire subtree of a parameter, including itself and all its descendants.

    `ancestors` is the chain of (class) types we've descended through from the root,
    used to detect recursive type cycles (e.g. self-referential classes).
    """

    root = TreeNode[Param](data=param, children=[])

    if is_parsable(param.normalized_hint):
        return root

    # About to recurse — check for cycle and extend the ancestor chain.
    cls = strip_optional(param.normalized_hint)
    if isinstance(cls, type) and cls in ancestors:
        raise RecursiveTypeError(
            param.name, shorten(param.normalized_hint), param.owning_obj_name
        )
    new_ancestors = (*ancestors, cls) if isinstance(cls, type) else ancestors

    for child_info in gather_children(param):
        child_node = gather_subtree(child_info, new_ancestors)
        child_node.parent = root
        root.children.append(child_node)
    return root


def leaves(nodes: list[TreeNode[T]]) -> Iterable[T]:
    for node in nodes:
        if not node.children:
            yield node.data
        else:
            yield from leaves(node.children)
