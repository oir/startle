import inspect
import re
from inspect import Parameter
from textwrap import dedent
from typing import Callable, get_args, get_origin, get_type_hints

from ._type_utils import _normalize_type, _shorten_type_annotation
from .args import Arg, Args, Name
from .error import ParserConfigError
from .value_parser import is_parsable


def _parse_docstring(func: Callable) -> tuple[str, dict[str, str]]:
    """
    Parse the docstring of a function and return the brief and the arg descriptions.
    """
    brief = ""
    arg_helps = {}
    docstring = inspect.getdoc(func)
    hints = get_type_hints(func)

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
        while lines[i].strip() != "Args:":  # find the Args section
            i += 1
            if i >= len(lines):
                break
        i += 1
        while i < len(lines) and lines[i].strip() != "":
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
                    if param in hints:
                        arg_helps[param] = desc

    return brief, arg_helps


def make_args(func: Callable, program_name: str = "") -> Args:
    # Get the signature of the function
    sig = inspect.signature(func)

    # Attempt to parse brief and arg descriptions from docstring
    brief, arg_helps = _parse_docstring(func)

    args = Args(brief=brief, program_name=program_name)

    used_short_names = set()

    for param_name, _ in sig.parameters.items():
        if param_name == "help":
            raise ParserConfigError(
                f"Cannot use `help` as parameter name in {func.__name__}()!"
            )

    # Discover if there are any named options that are of length 1
    # If so, those cannot be used as short names for other options
    for param_name, param in sig.parameters.items():
        if param.kind in [Parameter.KEYWORD_ONLY, Parameter.POSITIONAL_OR_KEYWORD]:
            if len(param_name) == 1:
                used_short_names.add(param_name)

    # Iterate over the parameters and add arguments based on kind
    for param_name, param in sig.parameters.items():
        normalized_annotation = _normalize_type(param.annotation)

        if param.default is not inspect.Parameter.empty:
            required = False
            default = param.default
        else:
            required = True
            default = None

        help = arg_helps.get(param_name, "")

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
            normalized_annotation = str
            container_type = list
        elif param.kind is Parameter.VAR_KEYWORD:
            nary = True
            normalized_annotation = str
            container_type = dict  # this is the only case that can be a dict

        # for n-ary options, type should refer to the inner type
        # if inner type is absent from the hint, assume str
        if get_origin(normalized_annotation) in [list, tuple, set]:
            nary = True
            args_ = get_args(normalized_annotation)
            container_type = get_origin(normalized_annotation)
            normalized_annotation = args_[0] if args_ else str
        elif normalized_annotation in [list, tuple, set]:
            nary = True
            container_type = normalized_annotation
            normalized_annotation = str

        if param.kind is not Parameter.VAR_KEYWORD and not is_parsable(
            normalized_annotation
        ):
            raise ParserConfigError(
                f"Unsupported type `{_shorten_type_annotation(param.annotation)}` "
                f"for parameter `{param_name}` in `{func.__name__}()`!"
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
            args.add_unknown_kwargs(arg)
        else:
            args.add(arg)

    return args
