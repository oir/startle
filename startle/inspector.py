from typing import get_type_hints, Callable, Optional, Union, get_origin, get_args
import inspect
from .args import Arg, Args, Name
import types
import re
from textwrap import dedent


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
            merged_lines = []
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
                args_desc = re.search(r"(\S+)(?:\s+\(.*?\))?:(.*)", line)
                param, desc = args_desc.groups()
                param = param.strip()
                desc = desc.strip()
                if param in hints:
                    arg_helps[param] = desc

    return brief, arg_helps


def make_args(func: Callable) -> Args:
    # Get the signature of the function
    sig = inspect.signature(func)

    # Attempt to parse brief and arg descriptions from docstring
    brief, arg_helps = _parse_docstring(func)

    args = Args(brief=brief)

    # Helper function to normalize type annotations
    def normalize_type(annotation):
        origin = get_origin(annotation)
        args = get_args(annotation)
        pod_types = {int, float, str, bool}
        if (
            (origin is Union or origin is types.UnionType)
            and len(args) == 2
            and type(None) in args
        ):
            return Optional[args[0] if args[1] is type(None) else args[1]]
        elif origin is None and annotation is not None:
            # Handle bar syntax (POD | None)
            for pod_type in pod_types:
                if annotation == Union[pod_type, None]:
                    return Optional[pod_type]
        return annotation

    used_short_names = set()

    # Discover if there are any named options that are of length 1
    # If so, those cannot be used as short names for other options
    for param_name, param in sig.parameters.items():
        if (
            param.kind == inspect.Parameter.KEYWORD_ONLY
            or param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        ):
            if len(param_name) == 1:
                used_short_names.add(param_name)

    # Iterate over the parameters and add arguments based on kind
    for param_name, param in sig.parameters.items():
        normalized_annotation = normalize_type(param.annotation)

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

        if (
            param.kind == inspect.Parameter.POSITIONAL_ONLY
            or param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        ):
            positional = True
        if (
            param.kind == inspect.Parameter.KEYWORD_ONLY
            or param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        ):
            named = True
            if len(param_name) == 1:
                name = Name(short=param_name_sub)
            elif param_name[0] not in used_short_names:
                name = Name(short=param_name_sub[0], long=param_name_sub)
                used_short_names.add(param_name_sub[0])
            else:
                name = Name(long=param_name_sub)

        # for n-ary options, type should refer to the inner type
        # if inner type is absent from the hint, assume str
        if get_origin(normalized_annotation) is list:
            nary = True
            args_ = get_args(normalized_annotation)
            normalized_annotation = args_[0] if args_ else str
        elif normalized_annotation is list:
            nary = True
            normalized_annotation = str

        arg = Arg(
            name=name,
            type_=normalized_annotation,
            metavar=metavar,
            help=help,
            required=required,
            default=default,
            is_positional=positional,
            is_named=named,
            is_nary=nary,
        )
        args.add(arg)

    return args
