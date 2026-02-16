from dataclasses import dataclass, field
from inspect import Parameter
from typing import Any

from .._docstr import ParamHelp
from .._type_utils import (
    TypeHint,
    normalize_annotation,
    strip_not_required,
    strip_required,
)
from .nary import get_naryness
from .typeddict import Missing


def is_positional(param: Parameter) -> bool:
    return param.kind in [
        Parameter.POSITIONAL_ONLY,
        Parameter.POSITIONAL_OR_KEYWORD,
        Parameter.VAR_POSITIONAL,
    ]


def is_keyword(param: Parameter) -> bool:
    return param.kind in [
        Parameter.KEYWORD_ONLY,
        Parameter.POSITIONAL_OR_KEYWORD,
        Parameter.VAR_KEYWORD,
    ]


def is_variadic(param: Parameter) -> bool:
    return param.kind in [Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD]


@dataclass(kw_only=True)
class ParamInfo:
    param: Parameter | str
    hint: TypeHint
    help: ParamHelp
    default: Any = None
    default_factory: Any = None
    is_required: bool

    normalized_annotation: TypeHint = field(init=False)
    container_type: type | None = field(init=False)
    nary: bool = field(init=False)

    owning_obj_name: str = ""

    def __post_init__(self):
        self.normalized_annotation = normalize_annotation(self.hint)

        param_or_annot = self.param if isinstance(self.param, Parameter) else self.hint
        self.nary, self.container_type, self.normalized_annotation = get_naryness(
            param_or_annot, self.normalized_annotation
        )

    @property
    def name(self) -> str:
        if isinstance(self.param, Parameter):
            return self.param.name
        else:
            assert isinstance(self.param, str)
            return self.param

    @property
    def is_positional(self) -> bool:
        return isinstance(self.param, Parameter) and is_positional(self.param)

    @property
    def is_keyword(self) -> bool:
        return isinstance(self.param, str) or is_keyword(self.param)

    @property
    def is_var_positional(self) -> bool:
        return (
            isinstance(self.param, Parameter)
            and self.param.kind == Parameter.VAR_POSITIONAL
        )

    @property
    def is_var_keyword(self) -> bool:
        return (
            isinstance(self.param, Parameter)
            and self.param.kind == Parameter.VAR_KEYWORD
        )

    @property
    def is_non_var_keyword(self) -> bool:
        """
        Whether this parameter is a non-variadic keyword parameter.
        """
        return self.is_keyword and not self.is_var_keyword

    @classmethod
    def from_param(
        cls,
        *,
        param: Parameter,
        hint: TypeHint,
        help: ParamHelp,
        default_factory: Any = None,
        owning_obj_name: str = "",
    ) -> "ParamInfo":
        required = param.default is Parameter.empty
        default = param.default if not required else None

        return ParamInfo(
            param=param,
            hint=hint,
            help=help,
            default=default,
            default_factory=default_factory,
            is_required=required,
            owning_obj_name=owning_obj_name,
        )

    @classmethod
    def from_td_param(
        cls,
        *,
        param_name: str,
        annotation: type,
        help: ParamHelp,
        in_required_keys: bool,
        in_optional_keys: bool,
        owning_obj_name: str = "",
    ) -> "ParamInfo":
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

        return ParamInfo(
            param=param_name,
            hint=normalized_annotation,
            help=help,
            default=Missing if not required else None,
            default_factory=None,
            is_required=required,
            owning_obj_name=owning_obj_name,
        )
