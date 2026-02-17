from collections.abc import Iterable
from dataclasses import dataclass, is_dataclass
from typing import Generic, TypeVar, cast, get_type_hints

from .._docstr import get_param_help, parse_docstring
from .._typing import is_typeddict, strip_optional
from .._value_parser import is_parsable
from .classes import get_class_initializer_params
from .dataclasses import get_default_factories
from .param import Param

T = TypeVar("T")


@dataclass(kw_only=True)
class TreeNode(Generic[T]):
    data: T
    children: list["TreeNode[T]"]
    parent: "TreeNode[T] | None" = None


def gather_children(param_info: Param) -> list[Param]:
    """
    Collect immediate children of a parameter, if any (non-recursively).
    """

    if is_parsable(param_info.normalized_annotation):
        # If parsable, we consider this a leaf node.
        return []

    param_info.check_recursable()

    cls = strip_optional(param_info.normalized_annotation)

    children: list[Param] = []
    if is_typeddict(cls):
        params = get_type_hints(cls, include_extras=True).items()
        optional_keys = cast(frozenset[str], cls.__optional_keys__)  # type: ignore
        required_keys = cast(frozenset[str], cls.__required_keys__)  # type: ignore
        _, arg_helps = parse_docstring(cls)

        for param_name, annotation in params:
            child_info = Param.from_td_param(
                param_name=param_name,
                annotation=annotation,
                help=get_param_help(param_name, annotation, arg_helps),
                in_required_keys=param_name in required_keys,
                in_optional_keys=param_name in optional_keys,
                owning_obj_name=cls.__name__,
            )
            children.append(child_info)
    else:
        # regular class
        assert isinstance(cls, type), "Unexpected type form that is not a type!"

        params = get_class_initializer_params(cls)
        hints = get_type_hints(cls.__init__, include_extras=True)
        _, arg_helps = parse_docstring(cls)
        default_factories = get_default_factories(cls) if is_dataclass(cls) else {}

        # odd pyright quirk, have to repeat this assert
        assert isinstance(cls, type), "Unexpected type form that is not a type!"

        for _, param in params:
            child_info = Param.from_param(
                param=param,
                hint=hints.get(param.name, str),
                help=get_param_help(param.name, param, arg_helps),
                default_factory=default_factories.get(param.name, None),
                owning_obj_name=cls.__name__,
            )
            children.append(child_info)

    return children


def gather_subtree(param_info: Param) -> TreeNode[Param]:
    """
    Collect the entire subtree of a parameter, including itself and all its descendants.
    """

    root = TreeNode[Param](data=param_info, children=[])
    for child_info in gather_children(param_info):
        child_node = gather_subtree(child_info)
        child_node.parent = root
        root.children.append(child_node)
    return root


def leaves(nodes: list[TreeNode[T]]) -> Iterable[T]:
    for node in nodes:
        if not node.children:
            yield node.data
        else:
            yield from leaves(node.children)
