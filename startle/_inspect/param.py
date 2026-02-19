from dataclasses import dataclass, field
from inspect import Parameter
from typing import Any, Literal, cast

from startle.error import (
    NaryNonRecursableParamError,
    NonClassNonRecursableParamError,
    VariadicNonRecursableParamError,
)

from .._docstr import ParamHelp
from .._typing import (
    TypeHint,
    normalize_annotation,
    shorten_type_annotation,
    strip_not_required,
    strip_optional,
    strip_required,
)
from ..args import Missing
from .nary import get_annotation_naryness

ParameterKind = Literal[
    # _ParameterKind is private, therefore we do this
    Parameter.POSITIONAL_ONLY,
    Parameter.POSITIONAL_OR_KEYWORD,
    Parameter.VAR_POSITIONAL,
    Parameter.KEYWORD_ONLY,
    Parameter.VAR_KEYWORD,
]


def is_positional(kind: ParameterKind | None) -> bool:
    return kind in [
        Parameter.POSITIONAL_ONLY,
        Parameter.POSITIONAL_OR_KEYWORD,
        Parameter.VAR_POSITIONAL,
    ]


def is_keyword(kind: ParameterKind | None) -> bool:
    return kind in [
        Parameter.KEYWORD_ONLY,
        Parameter.POSITIONAL_OR_KEYWORD,
        Parameter.VAR_KEYWORD,
    ]


def is_variadic(kind: ParameterKind | None) -> bool:
    return kind in [Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD]


def get_naryness(
    normalized_annotation: Any, kind: ParameterKind | None = None
) -> tuple[bool, type | None, Any]:
    """
    Get the n-ary status, container type, and normalized annotation for a parameter.
    For n-ary parameters, the type (updated `normalized_annotation`) will refer
    to the inner type.

    If inner type is absent from the hint, assume str.

    Returns:
        `nary`, `container_type`, and `normalized_annotation` as a tuple.
    """
    if kind == Parameter.VAR_POSITIONAL:
        return True, list, normalized_annotation

    return get_annotation_naryness(normalized_annotation)


@dataclass(kw_only=True)
class Param:
    """
    Represents a parameter with its metadata, either from a function signature or a TypedDict definition.

    Attributes:
        name: The name of the parameter.
        hint: The type hint of the parameter.
        help: The help information for the parameter, including description and short name.
        default: The default value of the parameter, if any.
        default_factory: The default factory for the parameter, if any (used for dataclasses).
        is_required: Whether the parameter is required.
            Note that TypedDict parameters can be required or optional regardless of whether they have defaults.
        kind: The kind of the parameter (positional-only, keyword-only, variadic, etc.), if this
            parameter comes from a function signature, None otherwise.
        normalized_annotation: The normalized type hint of the parameter, computed from `hint`.
        container_type: If the parameter is n-ary, the type of the container (e.g. list, tuple, set), None otherwise.
        is_nary: Whether the parameter is n-ary (e.g. *args, List[int], etc.), computed from `hint` and `kind`.
        owning_obj_name: The name of the owning object (function or class) for error messages.
    """

    name: str
    hint: TypeHint
    help: ParamHelp
    default: Any = None
    default_factory: Any = None
    is_required: bool
    kind: ParameterKind | None = None

    normalized_annotation: TypeHint = field(init=False)
    container_type: type | None = field(init=False)
    is_nary: bool = field(init=False)

    owning_obj_name: str = ""

    def __post_init__(self):
        self.normalized_annotation = normalize_annotation(self.hint)

        self.is_nary, self.container_type, self.normalized_annotation = get_naryness(
            self.normalized_annotation, self.kind
        )

    @property
    def is_positional(self) -> bool:
        return is_positional(self.kind)

    @property
    def is_keyword(self) -> bool:
        return self.kind is None or is_keyword(self.kind)

    @property
    def is_var_positional(self) -> bool:
        return self.kind == Parameter.VAR_POSITIONAL

    @property
    def is_var_keyword(self) -> bool:
        return self.kind == Parameter.VAR_KEYWORD

    @property
    def is_non_var_keyword(self) -> bool:
        """
        Whether this parameter is a non-variadic keyword parameter.
        """
        return self.is_keyword and not self.is_var_keyword

    def check_recursable(self) -> None:
        """
        Raise if the parameter cannot be recursed into, no-op otherwise.
        """
        if is_variadic(self.kind):
            raise VariadicNonRecursableParamError(self.name, self.owning_obj_name)
        if self.is_nary:
            raise NaryNonRecursableParamError(self.name, self.owning_obj_name)
        normalized_annotation = strip_optional(self.normalized_annotation)
        if not isinstance(normalized_annotation, type):
            raise NonClassNonRecursableParamError(
                self.name,
                shorten_type_annotation(self.normalized_annotation),
                self.owning_obj_name,
            )

    @classmethod
    def from_parameter(
        cls,
        *,
        parameter: Parameter,
        hint: TypeHint,
        help: ParamHelp | None = None,
        default_factory: Any = None,
        owning_obj_name: str = "",
    ) -> "Param":
        required = parameter.default is Parameter.empty
        default = parameter.default if not required else None

        return Param(
            name=parameter.name,
            hint=hint,
            help=help or ParamHelp(),
            default=default,
            default_factory=default_factory,
            is_required=required,
            kind=cast(ParameterKind, parameter.kind),
            owning_obj_name=owning_obj_name,
        )

    @classmethod
    def from_td_param(
        cls,
        *,
        param_name: str,
        annotation: type,
        help: ParamHelp | None = None,
        in_required_keys: bool,
        in_optional_keys: bool,
        owning_obj_name: str = "",
    ) -> "Param":
        is_required, normalized_annotation = strip_required(annotation)
        is_not_required, normalized_annotation = strip_not_required(
            normalized_annotation
        )
        normalized_annotation = normalize_annotation(normalized_annotation)

        required = in_required_keys or not in_optional_keys
        # NotRequired[] and Required[] are stronger than total=False/True
        if is_required:
            required = True
        elif is_not_required:
            required = False

        return Param(
            name=param_name,
            hint=normalized_annotation,
            help=help or ParamHelp(),
            default=Missing if not required else None,
            default_factory=None,
            is_required=required,
            kind=None,
            owning_obj_name=owning_obj_name,
        )
