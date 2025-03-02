import inspect
import re
from inspect import Parameter
from textwrap import dedent
from typing import (
    Callable,
    Iterable,
    Literal,
    get_args,
    get_origin,
)

from ._type_utils import _normalize_type, _shorten_type_annotation
from .arg import Arg, Name
from .args import Args
from .error import ParserConfigError
from .value_parser import is_parsable


def _parse_docstring(
    docstring: str, kind: Literal["function", "class"]
) -> tuple[str, dict[str, str]]:
    params_headers: list[str]
    if kind == "function":
        params_headers = ["Args:", "Arguments:"]
    else:
        params_headers = ["Attributes:"]

    brief = ""
    arg_helps: dict[str, str] = {}

    if docstring:
        lines = docstring.split("\n")

        # first, find the brief
        i = 0
        while i < len(lines) and lines[i].strip() != "":
            if brief:
                brief += " "
            brief += lines[i].strip()
            i += 1

        # first, find the Args section
        args_section = ""
        i = 0
        while lines[i].strip() not in params_headers:  # find the parameters section
            i += 1
            if i >= len(lines):
                break
        i += 1

        # then run through the lines until we find the first non-indented or empty line
        while i < len(lines) and lines[i].startswith(" ") and lines[i].strip() != "":
            args_section += lines[i] + "\n"
            i += 1

        if args_section:
            args_section = dedent(args_section).strip()

            # then, merge indented lines together
            merged_lines: list[str] = []
            for line in args_section.split("\n"):
                # if a line is indented, merge it with the previous line
                if line.lstrip() != line:
                    if not merged_lines:
                        return brief, {}
                    merged_lines[-1] += " " + line.strip()
                else:
                    merged_lines.append(line.strip())

            # now each line should be an arg description
            for line in merged_lines:
                if args_desc := re.search(r"(\S+)(?:\s+\(.*?\))?:(.*)", line):
                    param, desc = args_desc.groups()
                    param = param.strip()
                    desc = desc.strip()
                    arg_helps[param] = desc

    return brief, arg_helps


def _parse_func_docstring(func: Callable) -> tuple[str, dict[str, str]]:
    """
    Parse the docstring of a function and return the brief and the arg descriptions.
    """
    docstring = inspect.getdoc(func) or ""

    return _parse_docstring(docstring, "function")


def _parse_class_docstring(cls: type) -> dict[str, str]:
    """
    Parse the docstring of a class and return the arg descriptions.
    """
    docstring = inspect.getdoc(cls) or ""

    _, arg_helps = _parse_docstring(docstring, "class")

    return arg_helps


def make_args_from_params(
    params: Iterable[tuple[str, Parameter]],
    obj_name: str,
    brief: str = "",
    arg_helps: dict[str, str] = {},
    program_name: str = "",
) -> Args:
    args = Args(brief=brief, program_name=program_name)

    used_short_names = set()

    for param_name, _ in params:
        if param_name == "help":
            raise ParserConfigError(
                f"Cannot use `help` as parameter name in `{obj_name}`!"
            )

    # Discover if there are any named options that are of length 1
    # If so, those cannot be used as short names for other options
    for param_name, param in params:
        if param.kind in [Parameter.KEYWORD_ONLY, Parameter.POSITIONAL_OR_KEYWORD]:
            if len(param_name) == 1:
                used_short_names.add(param_name)

    # Iterate over the parameters and add arguments based on kind
    for param_name, param in params:
        normalized_annotation = (
            str
            if param.annotation is Parameter.empty
            else _normalize_type(param.annotation)
        )

        if param.default is not inspect.Parameter.empty:
            required = False
            default = param.default
        else:
            required = True
            default = None

        help = arg_helps.get(param_name, "")
        if param.kind is Parameter.VAR_KEYWORD:
            help = help or arg_helps.get(f"**{param_name}", "")

        param_name_sub = param_name.replace("_", "-")
        positional = False
        named = False
        name = Name(long=param_name_sub)
        metavar = ""
        nary = False
        container_type: type | None = None

        if param.kind in [
            Parameter.POSITIONAL_ONLY,
            Parameter.POSITIONAL_OR_KEYWORD,
            Parameter.VAR_POSITIONAL,
        ]:
            positional = True
        if param.kind in [
            Parameter.KEYWORD_ONLY,
            Parameter.POSITIONAL_OR_KEYWORD,
            Parameter.VAR_KEYWORD,
        ]:
            named = True
            if len(param_name) == 1:
                name = Name(short=param_name_sub)
            elif param_name[0] not in used_short_names:
                name = Name(short=param_name_sub[0], long=param_name_sub)
                used_short_names.add(param_name_sub[0])
            else:
                name = Name(long=param_name_sub)

        if param.kind is Parameter.VAR_POSITIONAL:
            nary = True
            container_type = list

        # for n-ary options, type should refer to the inner type
        # if inner type is absent from the hint, assume str

        orig = get_origin(normalized_annotation)
        args_ = get_args(normalized_annotation)

        if orig in [list, set]:
            nary = True
            container_type = orig
            normalized_annotation = args_[0] if args_ else str
        elif orig is tuple and len(args_) == 2 and args_[1] is ...:
            nary = True
            container_type = orig
            normalized_annotation = args_[0] if args_ else str
        elif normalized_annotation in [list, tuple, set]:
            nary = True
            container_type = normalized_annotation
            normalized_annotation = str

        if not is_parsable(normalized_annotation):
            raise ParserConfigError(
                f"Unsupported type `{_shorten_type_annotation(param.annotation)}` "
                f"for parameter `{param_name}` in `{obj_name}`!"
            )

        arg = Arg(
            name=name,
            type_=normalized_annotation,
            container_type=container_type,
            metavar=metavar,
            help=help,
            required=required,
            default=default,
            is_positional=positional,
            is_named=named,
            is_nary=nary,
        )
        if param.kind is Parameter.VAR_POSITIONAL:
            args.add_unknown_args(arg)
        elif param.kind is Parameter.VAR_KEYWORD:
            arg.name = Name(long="<key>")
            args.enable_var_kwargs(arg)
        else:
            args.add(arg)

    return args


def make_args_from_func(func: Callable, program_name: str = "") -> Args:
    # Get the signature of the function
    sig = inspect.signature(func)
    params = sig.parameters.items()

    # Attempt to parse brief and arg descriptions from docstring
    brief, arg_helps = _parse_func_docstring(func)

    return make_args_from_params(
        params, f"{func.__name__}()", brief, arg_helps, program_name
    )


def make_args_from_class(cls: type, program_name: str = "", brief: str = "") -> Args:
    # TODO: check if cls is a class?

    func = cls.__init__  # type: ignore
    # (mypy thinks cls is an instance)

    # Get the signature of the initializer
    sig = inspect.signature(func)

    # name of the first parameter (usually `self`)
    self_name = next(iter(sig.parameters))

    # filter out the first parameter
    params = [
        (name, param) for name, param in sig.parameters.items() if name != self_name
    ]

    # TODO: maybe for regular classes, parse from init, but for dataclasses, parse from the class itself?
    arg_helps = _parse_class_docstring(cls)

    return make_args_from_params(params, cls.__name__, brief, arg_helps, program_name)
