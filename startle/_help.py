"""
Utilities for prettifying and formatting of help messages.
"""

import sys
from enum import Enum
from typing import Any, Literal

from rich.text import Text

from .arg import Arg, Name
from .metavar import _get_metavar


class _Sty:
    name = "bold"
    pos_name = "bold"
    opt = "green"
    var = "blue"
    literal_var = ""
    title = "bold underline dim"


def name_usage(name: Name, kind: Literal["listing", "usage line"]) -> Text:
    """
    Format the name of an argument for either detailed options table (kind: listing)
    or the brief usage line (kind: usage line).
    """
    if kind == "listing":
        name_list = []
        if name.short:
            name_list.append(
                Text(f"-{name.short}", style=f"{_Sty.name} {_Sty.opt} not dim")
            )
        if name.long:
            name_list.append(
                Text(f"--{name.long}", style=f"{_Sty.name} {_Sty.opt} not dim")
            )
        return Text("|", style=f"{_Sty.opt} dim").join(name_list)
    else:
        if name.long:
            return Text(f"--{name.long}", style=f"{_Sty.name} {_Sty.opt}")
        else:
            return Text(f"-{name.short}", style=f"{_Sty.name} {_Sty.opt}")

def _meta(metavar: list[str] | str) -> Text:
    return (
        Text(metavar)
        if isinstance(metavar, str)
        else Text("|", style="dim").join(
            [Text(m, style=f"{_Sty.literal_var} not dim") for m in metavar]
        )
    )

def _repeated(text: Text) -> Text:
    repeat = Text("[") + text.copy() + " ...]"
    repeat.stylize("dim")
    return Text.assemble(text, " ", repeat)
    
def _pos_usage(name: Name, metavar: list[str] | str, is_nary: bool) -> Text:
    text = Text.assemble("<", (f"{name}:", _Sty.pos_name), _meta(metavar), ">")
    text.stylize(_Sty.var)
    if is_nary:
        text = _repeated(text)
    return text


def _opt_usage(name: Name, metavar: list[str] | str, is_nary: bool, kind: Literal["listing", "usage line"]) -> Text:
    if isinstance(metavar, list):
        option = _meta(metavar)
        option.stylize(_Sty.var)
    else:
        option = Text(f"<{metavar}>", style=_Sty.var)
    if is_nary:
        option = _repeated(option)
    return Text.assemble(name_usage(name, kind), " ", option)


def usage(arg: Arg, kind: Literal["listing", "usage line"] = "listing") -> Text:
    """
    Format an argument (possibly with its metavar) for either detailed options
    table (kind: listing) or the brief usage line (kind: usage line).
    """
    if arg.is_positional and not arg.is_named:
        text = _pos_usage(arg.name, arg.metavar, arg.is_nary)
    elif arg.is_flag:
        text = name_usage(arg.name, kind)
    else:
        text = _opt_usage(arg.name, arg.metavar, arg.is_nary, kind)

    if not arg.required and kind == "usage line":
        text = Text.assemble("[", text, "]")
    return text


def default_value(val: Any) -> str:
    if isinstance(val, str) and isinstance(val, Enum):
        return val.value
    if sys.version_info >= (3, 11):
        from enum import StrEnum

        if isinstance(val, StrEnum):
            return val.value
    if isinstance(val, Enum):
        return val.name.lower().replace("_", "-")
    return str(val)


def help(arg: Arg) -> Text:
    helptext = Text(arg.help, style="italic")
    delim = " " if helptext else ""
    if arg.is_flag:
        helptext = Text.assemble(helptext, delim, ("(flag)", _Sty.opt))
    elif arg.required:
        helptext = Text.assemble(helptext, delim, ("(required)", "yellow"))
    else:
        helptext = Text.assemble(
            helptext,
            delim,
            (f"(default: {default_value(arg.default)})", _Sty.opt),
        )
    return helptext


def var_kwargs_help(var_kwargs_type, var_kwargs_is_nary, kind: Literal["listing", "usage line"]) -> Text:
    kwargs_metavar = _get_metavar(var_kwargs_type)
    kwargs_meta = _meta(kwargs_metavar)
    if kind == "usage line":
        return _repeated(_opt_usage(Name("", "<key>"), kwargs_meta, var_kwargs_is_nary, kind))