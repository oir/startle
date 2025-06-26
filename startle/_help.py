"""
Utilities for prettifying and formatting of help messages.
"""

import sys
from enum import Enum
from typing import Any, Literal

from rich.text import Text

from .arg import Arg, Name


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

    def fmt(name: str, short: bool) -> Text:
        if name.startswith("<") and name.endswith(">"):
            # very special case for var kwargs.
            # TODO: maybe this should be done elsewhere / differently?
            name_ = name.strip("<>")
            return Text.assemble(
                ("--", f"{_Sty.name} {_Sty.opt} not dim"),
                ("<", "cyan not dim"),
                (name_, f"{_Sty.name} cyan not dim"),
                (">", "cyan not dim"),
            )
        return Text(
            f"-{name}" if short else f"--{name}",
            style=f"{_Sty.name} {_Sty.opt} not dim",
        )

    if kind == "listing":
        name_list = []
        if name.short:
            name_list.append(fmt(name.short, True))
        if name.long:
            name_list.append(fmt(name.long, False))
        return Text("|", style=f"{_Sty.opt} dim").join(name_list)
    else:
        if name.long:
            return fmt(name.long, False)
        else:
            return fmt(name.short, True)


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


def _pos_usage(arg: Arg) -> Text:
    text = Text.assemble("<", (f"{arg.name}:", _Sty.pos_name), _meta(arg.metavar), ">")
    text.stylize(_Sty.var)
    if arg.is_nary:
        text = _repeated(text)
    return text


def _opt_usage(arg: Arg, kind: Literal["listing", "usage line"]) -> Text:
    if isinstance(arg.metavar, list):
        option = _meta(arg.metavar)
        option.stylize(_Sty.var)
    else:
        option = Text(f"<{arg.metavar}>", style=_Sty.var)
    if arg.is_nary:
        option = _repeated(option)
    return Text.assemble(name_usage(arg.name, kind), " ", option)


def usage(arg: Arg, kind: Literal["listing", "usage line"] = "listing") -> Text:
    """
    Format an argument (possibly with its metavar) for either detailed options
    table (kind: listing) or the brief usage line (kind: usage line).
    """
    if arg.is_positional and not arg.is_named:
        text = _pos_usage(arg)
    elif arg.is_flag:
        if kind == "listing":
            text = Text.assemble(name_usage(arg.name, kind), " ")
        else:
            text = name_usage(arg.name, kind)
    else:
        text = _opt_usage(arg, kind)

    if not arg.required and kind == "usage line":
        text = Text.assemble("[", text, "]")
    return text


def default_value(val: Any) -> Text:
    if isinstance(val, str) and isinstance(val, Enum):
        return Text(val.value, style=_Sty.opt)
    if sys.version_info >= (3, 11):
        from enum import StrEnum

        if isinstance(val, StrEnum):
            return Text(val.value, style=_Sty.opt)
    if isinstance(val, Enum):
        return Text(val.name.lower().replace("_", "-"), style=_Sty.opt)
    if isinstance(val, str) and val == "":
        return Text('""', style=f"{_Sty.opt} dim")
    return Text(str(val), style=_Sty.opt)


def help(arg: Arg) -> Text:
    helptext = Text(arg.help, style="italic")
    delim = " " if helptext else ""
    if str(arg.name) == "":
        helptext = Text.assemble(
            helptext, delim, ("(unknown positional arguments)", "cyan")
        )
    elif arg.name.long == "<key>":
        helptext = Text.assemble(helptext, delim, ("(unknown options)", "cyan"))
    elif arg.is_flag:
        helptext = Text.assemble(helptext, delim, ("(flag)", _Sty.opt))
    elif arg.required:
        helptext = Text.assemble(helptext, delim, ("(required)", "yellow"))
    else:
        helptext = Text.assemble(
            helptext,
            delim,
            ("(default: ", _Sty.opt),
            default_value(arg.default),
            (")", _Sty.opt),
        )
    return helptext


def var_args_usage_line(arg: Arg) -> Text:
    return Text.assemble("[", _pos_usage(arg), "]")


def var_kwargs_usage_line(arg: Arg) -> Text:
    return Text.assemble("[", _repeated(_opt_usage(arg, "usage line")), "]")
