from dataclasses import asdict, dataclass
from typing import Any, Literal


@dataclass(kw_only=True)
class CommonConfig:
    """
    Common configuration for _inspect functions (internal).
    Used for brevity in function signatures.

    Attributes:
        obj_name: The name of the object being inspected (for error messages).
        recurse: Whether to recursively parse objects using their initializers.
        naming: How to name nested arguments when `recurse` is True.
            "flat" means all arguments are at the top level with their names (e.g. `--baz`),
            while "nested" means arguments are named using dot notation to indicate
            their nesting (e.g. `--foo.bar.baz`).
            Ignored if `recurse` is False.
        kw_only: Whether to make all arguments keyword-only, even if they are positional.
            This is used for children when recursing.
        parent_name: The name of the parent object, when recursing with nested naming.
    """

    obj_name: str = ""
    recurse: bool | Literal["child"] = False
    naming: Literal["flat", "nested"] = "flat"
    kw_only: bool = False
    parent_name: str = ""

    def __or__(self, other: "CommonConfig | dict[str, Any]") -> "CommonConfig":
        if isinstance(other, CommonConfig):
            other_dict = asdict(other)
        elif isinstance(other, dict):
            other_dict = other
        else:
            raise NotImplementedError(f"Cannot merge CommonConfig with {type(other)}")
        return CommonConfig(**(asdict(self) | other_dict))  # type: ignore

    def copy(self, **kwargs: Any) -> "CommonConfig":
        return self | kwargs
