import sys
from dataclasses import dataclass, field
from typing import Any, Literal

from .arg import Arg, Name
from .error import ParserConfigError, ParserOptionError


@dataclass
class Args:
    brief: str = ""

    _positional_args: list[Arg] = field(default_factory=list)
    _named_args: list[Arg] = field(default_factory=list)
    _name2idx: dict[str, int] = field(default_factory=dict)

    @staticmethod
    def _is_name(value: str) -> str | Literal[False]:
        """
        Check if a string, as provided in the command-line arguments, looks
        like an option name (starts with - or --).

        Returns:
            The name of the option if it is an option, otherwise False.
        """
        if value.startswith("--"):
            name = value[2:]
            if not name:
                raise ValueError("Prefix `--` not followed by an option!")
            return name
        if value.startswith("-"):
            name = value[1:]
            if not name:
                raise ValueError("Prefix `-` not followed by an option!")
            # ensure(
            #    len(name) == 1,
            #    "Options prefixed by `-` have to be short names! "
            #    "Did you mean `--" + name + "`?",
            # )
            return name
        return False

    def add(self, arg: Arg):
        """
        Add an argument to the parser.
        """
        if arg.is_positional:  # positional argument
            self._positional_args.append(arg)
        if arg.is_named:  # named argument
            if not arg.name.long_or_short:
                raise ParserConfigError(
                    "Named arguments should have at least one name!"
                )
            self._named_args.append(arg)
            if arg.name.short:
                self._name2idx[arg.name.short] = len(self._named_args) - 1
            if arg.name.long:
                self._name2idx[arg.name.long] = len(self._named_args) - 1

    def _parse(self, args: list[str]):
        idx = 0
        positional_idx = 0

        while idx < len(args):
            if name := self._is_name(args[idx]):
                if name in ["help", "h"]:
                    self.print_help()
                    sys.exit(0)
                if name not in self._name2idx:
                    raise ParserOptionError(f"Unexpected option `{name}`!")
                opt = self._named_args[self._name2idx[name]]
                if opt._parsed:
                    raise ParserOptionError(f"Option `{opt.name}` is multiply given!")

                if opt.is_flag:
                    opt.parse()
                    idx += 1
                elif opt.is_nary:
                    # n-ary option
                    values = []
                    idx += 1
                    while idx < len(args) and not self._is_name(args[idx]):
                        values.append(args[idx])
                        idx += 1
                    if not values:
                        raise ParserOptionError(f"Option `{name}` is missing argument!")
                    for value in values:
                        opt.parse(value)
                else:
                    # not a flag, not n-ary
                    if idx + 1 >= len(args):
                        raise ParserOptionError(f"Option `{name}` is missing argument!")
                    opt.parse(args[idx + 1])
                    idx += 2
            else:
                # this must be a positional argument

                # skip already parsed positional arguments
                # (because they could have also been named)
                while (
                    positional_idx < len(self._positional_args)
                    and self._positional_args[positional_idx]._parsed
                ):
                    positional_idx += 1

                if not positional_idx < len(self._positional_args):
                    raise ParserOptionError(
                        f"Unexpected positional argument: `{args[idx]}`!"
                    )

                arg = self._positional_args[positional_idx]
                if arg._parsed:
                    raise ParserOptionError(
                        f"Positional argument `{args[idx]}` is multiply given!"
                    )
                if arg.is_nary:
                    # n-ary positional arg
                    values = []
                    while idx < len(args) and not self._is_name(args[idx]):
                        values.append(args[idx])
                        idx += 1
                    for value in values:
                        arg.parse(value)
                else:
                    # regular positional arg
                    arg.parse(args[idx])
                    idx += 1
                positional_idx += 1

        # check if all required positional arguments are given
        for arg in self._positional_args:
            if not arg._parsed:
                if arg.required:
                    raise ParserOptionError(
                        f"Required positional argument <{arg.name.long}> is not provided!"
                    )
                else:
                    arg._value = arg.default
                    arg._parsed = True

        # check if all required named options are given
        for opt in self._named_args:
            if not opt._parsed:
                if opt.required:
                    raise ParserOptionError(
                        f"Required option `{opt.name}` is not provided!"
                    )
                else:
                    opt._value = opt.default
                    opt._parsed = True

    def make_func_args(self) -> tuple[list[Any], dict[str, Any]]:
        """
        Returns a tuple of positional arguments and named arguments, such that
        the function can be called like `func(*positional_args, **named_args)`.

        For arguments that are both positional and named, the named argument
        is preferred.
        """

        def var(opt: Arg) -> str:
            return opt.name.long_or_short.replace("-", "_")

        named_args = {var(opt): opt._value for opt in self._named_args}
        named_arg_values = list(named_args.values())
        positional_args = [
            arg._value
            for arg in self._positional_args
            if arg._value not in named_arg_values
        ]

        return positional_args, named_args

    def parse(self, args: list[str] | None = None) -> "Args":
        """
        Parse the command-line arguments.
        """
        if args is not None:
            self._parse(args)
        else:
            self._parse(sys.argv[1:])
        return self

    def print_help(self, console=None, program_name: str | None = None) -> None:
        """
        Print the help message to the console.
        """
        import sys

        from rich.console import Console
        from rich.table import Table
        from rich.text import Text

        name = program_name or sys.argv[0]

        positional_only = [
            arg
            for arg in self._positional_args
            if arg.is_positional and not arg.is_named
        ]
        positional_and_named = [
            arg for arg in self._positional_args if arg.is_positional and arg.is_named
        ]
        named_only = [
            opt for opt in self._named_args if opt.is_named and not opt.is_positional
        ]

        sty_name = "bold"
        sty_opt = "green"
        sty_var = "blue"
        sty_title = "bold underline dim"

        def name_usage(name: Name, kind: Literal["listing", "usage line"]) -> Text:
            if kind == "listing":
                name_list = []
                if name.short:
                    name_list.append(
                        Text(f"-{name.short}", style=f"{sty_name} {sty_opt}")
                    )
                if name.long:
                    name_list.append(
                        Text(f"--{name.long}", style=f"{sty_name} {sty_opt}")
                    )
                return Text(",").join(name_list)
            else:
                if name.long:
                    return Text(f"--{name.long}", style=f"{sty_name} {sty_opt}")
                else:
                    return Text(f"-{name.short}", style=f"{sty_name} {sty_opt}")

        def usage(arg: Arg, kind: Literal["listing", "usage line"] = "listing") -> Text:
            if arg.is_positional and not arg.is_named:
                text = Text.assemble(
                    "<", (f"{arg.name.long}:", sty_name), f"{arg.metavar}>"
                )
                text.stylize(sty_var)
                if arg.is_nary and kind == "usage line":
                    text += Text.assemble(" ", (f"[{text} ...]", "dim"))
            elif arg.is_flag:
                text = name_usage(arg.name, kind)
            else:
                option = Text(f"<{arg.metavar}>", style="blue")
                if arg.is_nary:
                    option += Text.assemble(" ", (f"[{option} ...]", "dim"))
                text = Text.assemble(name_usage(arg.name, kind), " ", option)

            if not arg.required and kind == "usage line":
                text = Text.assemble("[", text, "]")
            return text

        def help(arg: Arg) -> Text:
            helptext = Text(arg.help, style="italic")
            if arg.required:
                helptext = Text.assemble(helptext, " ", ("(required)", "yellow"))
            else:
                helptext = Text.assemble(
                    helptext, " ", (f"(default: {arg.default})", "green")
                )
            return helptext

        console = console or Console()
        if self.brief:
            console.print(self.brief + "\n")
        console.print(Text("Usage:", style=sty_title))
        console.print(
            Text(f"  {name} ")
            + Text(" ").join([usage(arg, "usage line") for arg in positional_only])
            + Text(" ")
            + Text(" ").join(
                [usage(opt, "usage line") for opt in positional_and_named + named_only]
            )
        )

        if positional_only + positional_and_named + named_only:
            console.print(Text("\nwhere", style=sty_title))

        table = Table(show_header=False, box=None, padding=(0, 0, 0, 2))

        for arg in positional_only:
            table.add_row("[dim](positional)[/dim]", usage(arg), help(arg))
        for opt in positional_and_named:
            table.add_row("[dim](pos. or opt.)[/dim]", usage(opt), help(opt))
        for opt in named_only:
            table.add_row("[dim](option)[/dim]", usage(opt), help(opt))

        console.print(table)

    def __repr__(self) -> str:
        rval = "<Args object>\n"
        for arg in self._positional_args:
            rval += f"  <positional> {arg.metavar}: {arg._value}\n"
        for arg in self._named_args:
            rval += f"  <named> {arg.name.long}: {arg._value}\n"
        return rval
