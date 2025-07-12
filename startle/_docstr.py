import inspect
import re
from dataclasses import dataclass
from textwrap import dedent
from typing import Callable, Literal


@dataclass
class _DocstrParam:
    desc: str = ""
    short_name: str | None = None


_DocstrParams = dict[str, _DocstrParam]


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
    # "param_name annotation: description"

    short_name_pattern = re.compile(r"(?:(?<=^)|(?<=\s))\[(\S)\](?:(?=\s)|(?=$))")
    # "[a]", "... [a] ...", etc


def _parse_docstring(
    docstring: str, kind: Literal["function", "class"]
) -> tuple[str, _DocstrParams]:
    params_headers = (
        _DocstrParts.function_params_headers
        if kind == "function"
        else _DocstrParts.class_params_headers
    )

    brief = ""
    arg_helps: _DocstrParams = {}

    if docstring:
        lines = docstring.split("\n")

        # first, find the brief
        i = 0
        while i < len(lines) and lines[i].strip() not in _DocstrParts.brief_enders:
            brief += lines[i].rstrip() + "\n"
            i += 1

        brief = "\n\n".join(
            paragraph.replace("\n", " ") for paragraph in brief.rstrip().split("\n\n")
        )

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
                    arg_helps[param] = _DocstrParam(desc=desc, short_name=short_name)

    return brief, arg_helps


def _parse_func_docstring(func: Callable) -> tuple[str, _DocstrParams]:
    """
    Parse the docstring of a function and return the brief and the arg descriptions.
    """
    docstring = inspect.getdoc(func) or ""

    return _parse_docstring(docstring, "function")


def _parse_class_docstring(cls: type) -> _DocstrParams:
    """
    Parse the docstring of a class and return the arg descriptions.
    """
    docstring = inspect.getdoc(cls) or ""

    _, arg_helps = _parse_docstring(docstring, "class")

    return arg_helps
