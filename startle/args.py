import sys
from dataclasses import dataclass, field
from typing import Any, Literal

from ._help import _Sty, help, usage, var_args_usage_line, var_kwargs_usage_line
from .arg import Arg, Name
from .error import ParserConfigError, ParserOptionError


@dataclass
class ParsingState:
    """
    A class to hold the state of the parsing process.
    """

    idx: int = 0
    positional_idx: int = 0

    # if `--` token is observed, all following arguments are treated as positional
    # even if they look like options (e.g. `--foo`). This attribute is used to
    # track that state.
    positional_only: bool = False


@dataclass
class Args:
    """
    A parser class to parse command-line arguments.
    Contains positional and named arguments, as well as var args
    (unknown positional arguments) and var kwargs (unknown options).
    """

    brief: str = ""
    program_name: str = ""

    _positional_args: list[Arg] = field(default_factory=list)
    _named_args: list[Arg] = field(default_factory=list)
    _name2idx: dict[str, int] = field(default_factory=dict)
    # note that _name2idx is many to one, because a name can be both short and long

    _var_args: Arg | None = None  # remaining unk args for functions with *args
    _var_kwargs: Arg | None = None  # remaining unk options for functions with **kwargs

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
            # if not name:
            #     raise ParserOptionError("Prefix `--` is not followed by an option!")
            # this case should not happen anymore
            return name
        if value.startswith("-"):
            name = value[1:]
            if not name:
                raise ParserOptionError("Prefix `-` is not followed by an option!")
            return name
        return False

    @staticmethod
    def _is_combined_short_names(value: str) -> str | Literal[False]:
        """
        Check if a string, as provided in the command-line arguments, looks
        like multiple combined short names (e.g. -abc).
        """
        if value.startswith("-") and not value.startswith("--"):
            value = value[1:].split("=", 1)[0]
            if len(value) > 1:
                return value
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

    def enable_unknown_args(self, arg: Arg) -> None:
        """
        Enable variadic positional arguments for parsing unknown positional arguments.
        This argument stores remaining positional arguments as if it was a list[T] type.
        """
        if arg.is_nary and arg.container_type is None:
            raise ParserConfigError(
                "Container type must be specified for n-ary options!"
            )
        self._var_args = arg

    def enable_unknown_opts(self, arg: Arg) -> None:
        """
        Enable variadic keyword arguments for parsing unknown named options.
        This Arg itself is not used to store anything, it is used as a reference to generate
        Arg objects as needed on the fly.
        """
        if arg.is_nary and arg.container_type is None:
            raise ParserConfigError(
                "Container type must be specified for n-ary options!"
            )
        self._var_kwargs = arg

    def _parse_equals_syntax(self, name: str, state: ParsingState) -> ParsingState:
        """
        Parse a cli argument as a named argument using the equals syntax (e.g. `--name=value`).
        Return new index after consuming the argument.
        This requires the argument to be not a flag.
        If the argument is n-ary, it can be repeated.
        """
        name, value = name.split("=", 1)
        normal_name = name.replace("_", "-")
        if normal_name not in self._name2idx:
            if self._var_kwargs:
                self.add(
                    Arg(
                        name=Name(long=normal_name),  # does long always work?
                        type_=self._var_kwargs.type_,
                        container_type=self._var_kwargs.container_type,
                        is_named=True,
                        is_nary=self._var_kwargs.is_nary,
                    )
                )
            else:
                raise ParserOptionError(f"Unexpected option `{name}`!")
        opt = self._named_args[self._name2idx[normal_name]]
        if opt._parsed and not opt.is_nary:
            raise ParserOptionError(f"Option `{opt.name}` is multiply given!")
        if opt.is_flag:
            raise ParserOptionError(
                f"Option `{opt.name}` is a flag and cannot be assigned a value!"
            )
        opt.parse(value)
        state.idx += 1
        return state

    def _parse_combined_short_names(
        self, names: str, args: list[str], state: ParsingState
    ) -> ParsingState:
        """
        Parse a cli argument as a combined short names (e.g. -abc).
        Return new index after consuming the argument.
        """
        for i, name in enumerate(names):
            if name == "?":
                self.print_help()
                raise SystemExit(0)
            if name not in self._name2idx:
                raise ParserOptionError(f"Unexpected option `{name}`!")
            opt = self._named_args[self._name2idx[name]]
            if opt._parsed and not opt.is_nary:
                raise ParserOptionError(f"Option `{opt.name}` is multiply given!")

            if i < len(names) - 1:
                # up until the last option, all options must be flags
                if not opt.is_flag:
                    raise ParserOptionError(
                        f"Option `{opt.name}` is not a flag and cannot be combined!"
                    )
                opt.parse()
            else:
                # last option can be a flag or a regular option
                if "=" in args[state.idx]:
                    value = args[state.idx].split("=", 1)[1]
                    last = f"{name}={value}"
                    return self._parse_equals_syntax(last, state)
                if opt.is_flag:
                    opt.parse()
                    state.idx += 1
                    return state
                if opt.is_nary:
                    # n-ary option
                    values = []
                    state.idx += 1
                    while state.idx < len(args) and self._is_name(args[state.idx]) is False:
                        values.append(args[state.idx])
                        state.idx += 1
                    if not values:
                        raise ParserOptionError(
                            f"Option `{opt.name}` is missing argument!"
                        )
                    for value in values:
                        opt.parse(value)
                    return state
                # not a flag, not n-ary
                if state.idx + 1 >= len(args):
                    raise ParserOptionError(f"Option `{opt.name}` is missing argument!")
                opt.parse(args[state.idx + 1])
                state.idx += 2
                return state

        raise RuntimeError("Programmer error: should not reach here!")

    def _parse_named(
        self, name: str, args: list[str], state: ParsingState
    ) -> ParsingState:
        """
        Parse a cli argument as a named argument / option.
        Return new index after consuming the argument.
        """
        if name in ["help", "?"]:
            self.print_help()
            raise SystemExit(0)
        if "=" in name:
            return self._parse_equals_syntax(name, state)
        normal_name = name.replace("_", "-")
        if normal_name not in self._name2idx:
            if self._var_kwargs:
                assert self._var_kwargs.type_ is not None
                self.add(
                    Arg(
                        name=Name(long=normal_name),  # does long always work?
                        type_=self._var_kwargs.type_,
                        container_type=self._var_kwargs.container_type,
                        is_named=True,
                        is_nary=self._var_kwargs.is_nary,
                    )
                )
            else:
                raise ParserOptionError(f"Unexpected option `{name}`!")
        opt = self._named_args[self._name2idx[normal_name]]
        if opt._parsed and not opt.is_nary:
            raise ParserOptionError(f"Option `{opt.name}` is multiply given!")

        if opt.is_flag:
            opt.parse()
            state.idx += 1
            return state
        if opt.is_nary:
            # n-ary option
            values = []
            state.idx += 1
            while state.idx < len(args) and self._is_name(args[state.idx]) is False:
                values.append(args[state.idx])
                state.idx += 1
            if not values:
                raise ParserOptionError(f"Option `{opt.name}` is missing argument!")
            for value in values:
                opt.parse(value)
            return state

        # not a flag, not n-ary
        if state.idx + 1 >= len(args):
            raise ParserOptionError(f"Option `{opt.name}` is missing argument!")
        opt.parse(args[state.idx + 1])
        state.idx += 2
        return state

    def _parse_positional(self, args: list[str], state: ParsingState) -> ParsingState:
        """
        Parse a cli argument as a positional argument.
        Return new indices after consuming the argument.
        """

        # skip already parsed positional arguments
        # (because they could have also been named)
        while (
            state.positional_idx < len(self._positional_args)
            and self._positional_args[state.positional_idx]._parsed
        ):
            state.positional_idx += 1

        if not state.positional_idx < len(self._positional_args):
            if self._var_args:
                self._var_args.parse(args[state.idx])
                state.idx += 1
                return state
            else:
                raise ParserOptionError(
                    f"Unexpected positional argument: `{args[state.idx]}`!"
                )

        arg = self._positional_args[state.positional_idx]
        if arg._parsed:
            raise ParserOptionError(
                f"Positional argument `{args[state.idx]}` is multiply given!"
            )
        if arg.is_nary:
            # n-ary positional arg
            values = []
            while state.idx < len(args) and self._is_name(args[state.idx]) is False:
                values.append(args[state.idx])
                state.idx += 1
            for value in values:
                arg.parse(value)
        else:
            # regular positional arg
            arg.parse(args[state.idx])
            state.idx += 1
        state.positional_idx += 1
        return state

    def _parse(self, args: list[str]):
        state = ParsingState()

        while state.idx < len(args):
            if not state.positional_only and args[state.idx] == "--":
                # all subsequent arguments will be attempted to be parsed as positional
                state.positional_only = True
                state.idx += 1
                continue
            name = self._is_name(args[state.idx])
            if not state.positional_only and name:
                # this must be a named argument / option
                if names := self._is_combined_short_names(args[state.idx]):
                    state = self._parse_combined_short_names(names, args, state)
                else:
                    try:
                        state = self._parse_named(name, args, state)
                    except ParserOptionError as e:
                        if self._var_args and str(e).startswith("Unexpected option"):
                            self._var_args.parse(args[state.idx])
                            state.idx += 1
                        else:
                            raise
            else:
                # this must be a positional argument
                state = self._parse_positional(args, state)

        # check if all required arguments are given, assign defaults otherwise
        for arg in self._positional_args + self._named_args:
            if not arg._parsed:
                if arg.required:
                    if arg.is_named:
                        # if a positional arg is also named, prefer this type of error message
                        raise ParserOptionError(
                            f"Required option `{arg.name}` is not provided!"
                        )
                    else:
                        raise ParserOptionError(
                            f"Required positional argument <{arg.name.long}> is not provided!"
                        )
                else:
                    arg._value = arg.default
                    arg._parsed = True

    def make_func_args(self) -> tuple[list[Any], dict[str, Any]]:
        """
        Transform parsed arguments into function arguments.

        Returns a tuple of positional arguments and named arguments, such that
        the function can be called like `func(*positional_args, **named_args)`.

        For arguments that are both positional and named, the positional argument
        is preferred, to handle variadic args correctly.
        """

        def var(opt: Arg | str) -> str:
            if isinstance(opt, str):
                return opt.replace("-", "_")
            return opt.name.long_or_short.replace("-", "_")

        positional_args = [arg._value for arg in self._positional_args]
        named_args = {
            var(opt): opt._value
            for opt in self._named_args
            if opt not in self._positional_args
        }

        if self._var_args and self._var_args._value:
            positional_args += self._var_args._value

        return positional_args, named_args

    def parse(self, cli_args: list[str] | None = None) -> "Args":
        """
        Parse the command-line arguments.

        Args:
            cli_args: The arguments to parse. If None, uses the arguments from the CLI.
        Returns:
            Self, for chaining.
        """
        if cli_args is not None:
            self._parse(cli_args)
        else:
            self._parse(sys.argv[1:])
        return self

    def print_help(self, console=None, usage_only: bool = False) -> None:
        """
        Print the help message to the console.

        Args:
            console: A rich console to print to. If None, uses the default console.
            usage_only: Whether to print only the usage line.
        """
        import sys

        from rich.console import Console
        from rich.table import Table
        from rich.text import Text

        name = self.program_name or sys.argv[0]

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

        # (1) print brief if it exists
        console = console or Console()
        console.print()
        if self.brief and not usage_only:
            console.print(self.brief + "\n")

        # (2) then print usage line
        console.print(Text("Usage:", style=_Sty.title))
        usage_components = [Text(f"  {name}")]
        pos_only_str = Text(" ").join(
            [usage(arg, "usage line") for arg in positional_only]
        )
        if pos_only_str:
            usage_components.append(pos_only_str)
        for opt in positional_and_named:
            usage_components.append(usage(opt, "usage line"))
        if self._var_args:
            usage_components.append(var_args_usage_line(self._var_args))
        for opt in named_only:
            usage_components.append(usage(opt, "usage line"))
        if self._var_kwargs:
            usage_components.append(var_kwargs_usage_line(self._var_kwargs))

        console.print(Text(" ").join(usage_components))

        if usage_only:
            console.print()
            return

        # (3) then print help message for each argument
        console.print(Text("\nwhere", style=_Sty.title))

        table = Table(show_header=False, box=None, padding=(0, 0, 0, 2))

        for arg in positional_only:
            table.add_row("[dim](positional)[/dim]", usage(arg), help(arg))
        for opt in positional_and_named:
            table.add_row("[dim](pos. or opt.)[/dim]", usage(opt), help(opt))
        if self._var_args:
            table.add_row(
                "[dim](positional)[/dim]",
                usage(self._var_args),
                help(self._var_args),
            )
        for opt in named_only:
            table.add_row("[dim](option)[/dim]", usage(opt), help(opt))
        if self._var_kwargs:
            table.add_row(
                "[dim](option)[/dim]",
                usage(self._var_kwargs),
                help(self._var_kwargs),
            )

        table.add_row(
            "[dim](option)[/dim]",
            Text.assemble(
                ("-?", f"{_Sty.name} {_Sty.opt} dim"),
                ("|", f"{_Sty.opt} dim"),
                ("--help", f"{_Sty.name} {_Sty.opt} dim"),
            ),
            "[i dim]Show this help message and exit.[/]",
        )

        console.print(table)
        console.print()
