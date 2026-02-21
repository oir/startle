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
    normalize,
    shorten,
    strip_container,
    strip_not_required,
    strip_optional,
    strip_required,
)
from ..args import Missing

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
        normalized_hint: The normalized type hint of the parameter, computed from `hint`.
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

    normalized_hint: TypeHint = field(init=False)
    container_type: type | None = None
    is_nary: bool = False

    owning_obj_name: str = ""

    def __post_init__(self):
        self.normalized_hint = normalize(self.hint)

        if self.kind == Parameter.VAR_POSITIONAL:
            self.is_nary = True
            self.container_type = list
        else:
            self.container_type, self.normalized_hint = strip_container(
                self.normalized_hint
            )
            self.is_nary = self.container_type is not None

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
        normalized_hint = strip_optional(self.normalized_hint)
        if not isinstance(normalized_hint, type):
            raise NonClassNonRecursableParamError(
                self.name,
                shorten(self.normalized_hint),
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
        normalized_annotation = normalize(normalized_annotation)

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
