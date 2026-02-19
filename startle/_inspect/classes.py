from collections.abc import Iterable
from dataclasses import MISSING, fields, is_dataclass
from inspect import Parameter, signature
from typing import Any


def get_initializer_parameters(cls: type) -> Iterable[tuple[str, Parameter]]:
    """
    Get the parameters of the class's `__init__` method, excluding `self`.
    """
    func = cls.__init__  # type: ignore

    # Get the signature of the initializer
    sig = signature(func)

    # name of the first parameter (usually `self`)
    self_name = next(iter(sig.parameters))

    # filter out the first parameter
    return [
        (name, param) for name, param in sig.parameters.items() if name != self_name
    ]


def get_default_factories(cls: type) -> dict[str, Any]:
    """
    Get the default factory functions for all fields in a dataclass.
    Note that this _excludes_ fields with a default value; only fields
    with a default factory are included.
    """
    if not is_dataclass(cls):
        raise ValueError(f"{cls} is not a dataclass")

    return {
        f.name: f.default_factory
        for f in fields(cls)
        if f.default_factory is not MISSING
    }
