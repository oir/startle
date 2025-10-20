import inspect
import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import singledispatch
from textwrap import dedent
from typing import Any, Literal


@dataclass
class ParamHelp:
    desc: str = ""
    short_name: str | None = None


ParamHelps = dict[str, ParamHelp]


class _DocstrParts:
    function_params_headers = ["Args:", "Arguments:"]
    class_params_headers = ["Attributes:"]
    brief_enders = [
        "Args:",
        "Arguments:",
        "Returns:",
        "Yields:",
        "Raises:",
        "Attributes:",
    ]

    param_pattern = re.compile(r"(\S+)(?:\s+(.*?))?:(.*)")
    # "param_name annotation: description", annotation optional

    short_name_pattern = re.compile(r"(?:(?<=^)|(?<=\s))\[(\S)\](?:(?=\s)|(?=$))")
    # "[a]", "... [a] ...", etc


def _parse_docstring(
    docstring: str, kind: Literal["function", "class"]
) -> tuple[str, ParamHelps]:
    params_headers = (
        _DocstrParts.function_params_headers
        if kind == "function"
        else _DocstrParts.class_params_headers
    )

    brief = ""
    arg_helps: ParamHelps = {}

    if docstring:
        lines = docstring.split("\n")

        # first, find the brief
        i = 0
        while i < len(lines) and lines[i].strip() not in _DocstrParts.brief_enders:
            brief += lines[i].rstrip() + "\n"
            i += 1

        brief = brief.rstrip()

        # then, find the Args section
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
                # attempt to parse like "param_name annotation: description"
                if args_desc := _DocstrParts.param_pattern.search(line):
                    param, annot, desc = args_desc.groups()
                    param = param.strip()
                    annot = annot.strip() if annot else ""
                    desc = desc.strip()
                    short_name: str | None = None
                    if short_name_match := _DocstrParts.short_name_pattern.search(
                        annot
                    ):
                        short_name = short_name_match.group(1)
                    arg_helps[param] = ParamHelp(desc=desc, short_name=short_name)

    return brief, arg_helps


@singledispatch
def parse_docstring(obj: Callable[..., Any] | type) -> tuple[str, ParamHelps]:
    """
    Parse the docstring of a function or class and return the brief and the arg descriptions.
    """
    raise NotImplementedError(f"parse_docstring not implemented for type {type(obj)}")


@parse_docstring.register(Callable)  # type: ignore
def _(func: Callable[..., Any]) -> tuple[str, ParamHelps]:
    """
    Parse the docstring of a function and return the brief and the arg descriptions.
    """
    docstring = inspect.getdoc(func) or ""

    return _parse_docstring(docstring, "function")


@parse_docstring.register
def _(cls: type) -> tuple[str, ParamHelps]:
    """
    Parse the docstring of a class and return the arg descriptions.
    """
    docstring = inspect.getdoc(cls) or ""

    return _parse_docstring(docstring, "class")
