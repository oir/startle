from dataclasses import MISSING, fields, is_dataclass
from typing import Any


def get_default_factories(cls: type) -> dict[str, Any]:
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
