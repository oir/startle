import sys
from typing import Literal, Any
from dataclasses import dataclass, field


class ParserOptionError(Exception):
    pass


class ParserValueError(ValueError):
    pass


class ParserConfigError(Exception):
    pass


@dataclass
class ValueParser:
    value: str

    def to_str(self) -> str:
        return self.value

    def to_int(self) -> int:
        try:
            return int(self.value)
        except ValueError as err:
            raise ParserValueError(
                f"Cannot parse integer from `{self.value}`!"
            ) from err

    def to_float(self) -> float:
        try:
            return float(self.value)
        except ValueError as err:
            raise ParserValueError(f"Cannot parse float from `{self.value}`!") from err

    def to_bool(self) -> bool:
        if self.value.lower() in {"true", "t", "yes", "y", "1"}:
            return True
        if self.value.lower() in {"false", "f", "no", "n", "0"}:
            return False
        raise ParserValueError(f"Cannot parse boolean from `{self.value}`!")

    def convert(self, type_: type) -> Any:
        # check if a method named `to_<type_.__name__>` exists
        method_name = f"to_{type_.__name__}"
        if hasattr(self, method_name):
            return getattr(self, method_name)()
        raise ParserValueError(f"Cannot parse argument to type {type_.__name__}!")


_default_metavars = {
    int: "int",
    str: "text",
    bool: "true|false",
}


@dataclass
class Arg:
    type_: type
    help: str = ""
    metavar: str = ""
    default: Any = None
    required: bool = False

    # Note: an Arg can be both positional and named.
    names: list[str] | None = None
    is_positional: bool = False

    _parsed: bool = False  # if this is already parsed
    _nargs: bool = False  # if this is n-ary

    _value: Any = None  # the parsed value

    @property
    def is_flag(self) -> bool:
        return self.type_ is bool and self.default is False and not self.is_positional

    def __post_init__(self):
        if not self.metavar:
            self.metavar = _default_metavars.get(self.type_, "val")

    def parse(self, value: str | None = None):
        if self.is_flag:
            assert value is None, "Flag options should not have values!"
            self._value = True
            self._parsed = True
        else:
            assert value is not None, "Non-flag options should have values!"
            self._value = ValueParser(value).convert(self.type_)
            self._parsed = True


@dataclass
class Args:
    brief: str = ""

    _positional_args: list[Arg] = field(default_factory=list)
    _named_args: list[Arg] = field(default_factory=list)
    _name2idx: dict[str, int] = field(default_factory=dict)

    @staticmethod
    def is_name(value: str) -> str | Literal[False]:
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

    def add(
        self,
        type_: type,
        positional: bool = False,
        names: list[str] | None = None,
        metavar: str = "",
        help: str = "",
        required: bool = False,
        default: Any = None,
    ):
        arg = Arg(
            type_=type_,
            metavar=metavar,
            help=help,
            required=required,
            default=default,
            names=names,
            is_positional=positional,
        )
        if not positional and not names:
            raise ParserConfigError(
                "Either positional or named arguments should be provided!"
            )
        if positional:  # positional argument
            self._positional_args.append(arg)
        if names:  # named argument
            self._named_args.append(arg)
            for name in names:
                self._name2idx[name] = len(self._named_args) - 1

    def _parse(self, args: list[str]):
        idx = 0
        positional_idx = 0

        while idx < len(args):
            if name := self.is_name(args[idx]):
                if name == "help":
                    self.print_help()
                    sys.exit(0)
                if name not in self._name2idx:
                    raise ParserOptionError(f"Unexpected option `{name}`!")
                opt = self._named_args[self._name2idx[name]]
                if opt._parsed:
                    raise ParserOptionError(f"Option `{name}` is multiply given!")

                if opt.is_flag:
                    opt.parse()
                    idx += 1
                # TODO: n-aries
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
                arg.parse(args[idx])
                idx += 1
                positional_idx += 1

        # check if all required positional arguments are given
        for arg in self._positional_args:
            if not arg._parsed:
                if arg.required:
                    raise ParserOptionError(
                        f"Required positional argument <{arg.metavar}> is not provided!"
                    )
                else:
                    arg._value = arg.default
                    arg._parsed = True

        # check if all required named options are given
        for opt in self._named_args:
            if not opt._parsed:
                if opt.required:
                    raise ParserOptionError(
                        f"Required option <{','.join(opt.names)}> is not provided!"
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
        named_args = {opt.names[-1]: opt._value for opt in self._named_args}
        named_arg_values = list(named_args.values())
        positional_args = [
            arg._value
            for arg in self._positional_args
            if arg._value not in named_arg_values
        ]

        return positional_args, named_args

    def parse(self, args: list[str] | None = None) -> "Args":
        if args is not None:
            self._parse(args)
        else:
            self._parse(sys.argv[1:])
        return self

    def print_help(self):
        from rich.console import Console
        from rich.table import Table
        from rich.text import Text

        import sys

        name = sys.argv[0]

        positional_only = [
            arg for arg in self._positional_args if arg.is_positional and not arg.names
        ]
        positional_and_named = [
            arg for arg in self._positional_args if arg.is_positional and arg.names
        ]
        named_only = [
            opt for opt in self._named_args if opt.names and not opt.is_positional
        ]

        def usage(arg: Arg, show_optional: bool = False) -> Text:
            if arg.is_positional and not arg.names:
                inner = Text(arg.metavar, style="bold")
                text = Text.assemble("<", inner, ">")
            elif arg.is_flag:
                text = Text.assemble("--", (arg.names[-1], "bold"))
            else:
                inner = arg.metavar
                text = Text.assemble("--", (arg.names[-1], "bold")) + Text.assemble(
                    " <", inner, ">"
                )

            if not arg.required and show_optional:
                text = Text.assemble("[", text, "]")
            return text

        def help(arg: Arg) -> Text:
            helptext = Text(arg.help, style="italic")
            if arg.required:
                helptext = Text.assemble(helptext, (" (required)", "yellow"))
            else:
                helptext = Text.assemble(
                    helptext, (f" (default: {arg.default})", "green")
                )
            return helptext

        console = Console()
        if self.brief:
            console.print(self.brief + "\n")
        console.print(Text("Usage:", style="underline dim"))
        console.print(
            Text(f"  {name} ")
            + Text(" ").join(
                [usage(arg, show_optional=True) for arg in positional_only]
            )
            + Text(" ")
            + Text(" ").join(
                [
                    usage(opt, show_optional=True)
                    for opt in positional_and_named + named_only
                ]
            )
        )

        if positional_only + positional_and_named + named_only:
            console.print(Text("\nwhere", style="underline dim"))

        table = Table(show_header=False, box=None, padding=(0, 0, 0, 2))

        if positional_only:
            for arg in positional_only:
                table.add_row(usage(arg), help(arg))

        if positional_and_named + named_only:
            for opt in positional_and_named + named_only:
                table.add_row(usage(opt), help(opt))

        console.print(table)

    def __repr__(self) -> str:
        rval = "<Args object>\n"
        for arg in self._positional_args:
            rval += f"  <positional> {arg.metavar}: {arg._value}\n"
        for arg in self._named_args:
            rval += f"  <named> {','.join(arg.names)}: {arg._value}\n"
        return rval
