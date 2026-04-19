import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from ._help import (
    Sty,
    help,
    usage,
    var_args_usage_line,
    var_kwargs_usage_line,
    wrap_usage,
)
from .arg import Arg, Name
from .error import (
    DuplicateOptionError,
    DuplicatePositionalArgumentError,
    FlagWithValueError,
    MissingContainerTypeError,
    MissingNameError,
    MissingOptionNameError,
    MissingOptionValueError,
    MissingRequiredOptionError,
    MissingRequiredPositionalArgumentError,
    NonFlagInShortNameCombinationError,
    UnexpectedOptionError,
    UnexpectedPositionalArgumentError,
)

if TYPE_CHECKING:
    from rich.console import Console


@dataclass
class _ParsingState:
    """
    A class to hold the state of the parsing process.
    """

    idx: int = 0
    positional_idx: int = 0

    # if `--` token is observed, all following arguments are treated as positional
    # even if they look like options (e.g. `--foo`). This attribute is used to
    # track that state.
    positional_only: bool = False


class Missing:
    """
    A sentinel class to represent a missing value.
    Used to differentiate between None as a value and no value provided.
    This is used for TypedDict optional keys, where instead of using None as
    a value for the key, the key is simply not present.
    """

    pass


@dataclass
class Args:
    """
    A parser class to parse command-line arguments.
    Contains positional and named arguments, as well as var args
    (unknown positional arguments) and var kwargs (unknown options).
    """

    brief: str = ""
    program_name: str = ""

    _positional_args: list[Arg] = field(default_factory=list[Arg])
    _named_args: list[Arg] = field(default_factory=list[Arg])
    _name2idx: dict[str, int] = field(default_factory=dict[str, int])
    # note that _name2idx is many to one, because a name can be both short and long

    _var_args: Arg | None = None  # remaining unk args for functions with *args
    _var_kwargs: Arg | None = None  # remaining unk options for functions with **kwargs
    _parent: "Args | None" = None  # parent Args instance

    @property
    def _args(self) -> list[Arg]:
        """
        Uniquely listed arguments. Note that an argument can be both positional and named,
        hence be in both lists.
        """
        seen = set[int]()
        unique_args: list[Arg] = []
        for arg in self._positional_args + self._named_args:
            if id(arg) not in seen:
                unique_args.append(arg)
                seen.add(id(arg))
        return unique_args

    @property
    def _children(self) -> Iterable["tuple[Arg, Args]"]:
        """
        Yield all child Args instances. Only relevant when parsing recursively.
        """
        for arg in self._args:
            if arg.args:
                yield arg, arg.args

    def _any_parsed_leaf(self) -> bool:
        """
        Return True if any leaf argument in this subtree has been parsed (via
        user input). Relies on `_check_completion` being structured so that
        defaults are assigned only after all required args are validated, so
        `is_parsed` on a leaf reliably means "the user provided it".
        """
        for arg in self._args:
            if arg.args is None:
                if arg.is_parsed:
                    return True
            elif arg.args._any_parsed_leaf():
                return True
        return False

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
            return name
        if value.startswith("-"):
            name = value[1:]
            if not name:
                raise MissingOptionNameError()
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

    def _find_arg_by_name(self, name: str) -> Arg | None:
        """
        Find an argument by its name (short or long) among self or the children.
        Returns the Arg if found, otherwise None.
        """
        if name in self._name2idx:
            return self._named_args[self._name2idx[name]]
        for _, child_args in self._children:
            result = child_args._find_arg_by_name(name)
            if result is not None:
                return result
        return None

    def add(self, arg: Arg):
        """
        Add an argument to the parser.
        """
        if arg.is_positional:  # positional argument
            self._positional_args.append(arg)
        if arg.is_named:  # named argument
            if not arg.name.long_or_short:
                raise MissingNameError()
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
            raise MissingContainerTypeError()
        self._var_args = arg

    def enable_unknown_opts(self, arg: Arg) -> None:
        """
        Enable variadic keyword arguments for parsing unknown named options.
        This Arg itself is not used to store anything, it is used as a reference to generate
        Arg objects as needed on the fly.
        """
        if arg.is_nary and arg.container_type is None:
            raise MissingContainerTypeError()
        self._var_kwargs = arg

    def _parse_equals_syntax(self, name: str, state: _ParsingState) -> _ParsingState:
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
                raise UnexpectedOptionError(name)
        opt = self._named_args[self._name2idx[normal_name]]
        if opt.is_parsed and not opt.is_nary:
            raise DuplicateOptionError(str(opt.name))
        if opt.is_flag:
            raise FlagWithValueError(str(opt.name))
        opt.parse(value)
        state.idx += 1
        return state

    def _parse_combined_short_names(
        self, names: str, args: list[str], state: _ParsingState
    ) -> _ParsingState:
        """
        Parse a cli argument as a combined short names (e.g. -abc).
        Return new index after consuming the argument.
        """
        for i, name in enumerate(names):
            if name == "?":
                self.print_help()
                raise SystemExit(0)
            opt = self._find_arg_by_name(name)
            if opt is None:
                raise UnexpectedOptionError(name)
            if opt.is_parsed and not opt.is_nary:
                raise DuplicateOptionError(str(opt.name))

            if i < len(names) - 1:
                # up until the last option, all options must be flags
                if not opt.is_flag:
                    raise NonFlagInShortNameCombinationError(str(opt.name))
                opt.parse()
            else:
                # last option can be a flag or a regular option
                if "=" in args[state.idx]:
                    if opt.is_flag:
                        raise FlagWithValueError(str(opt.name))
                    value = args[state.idx].split("=", 1)[1]
                    opt.parse(value)
                    state.idx += 1
                    return state
                if opt.is_flag:
                    opt.parse()
                    state.idx += 1
                    return state
                if opt.is_nary:
                    # n-ary option
                    values: list[str] = []
                    state.idx += 1
                    while (
                        state.idx < len(args)
                        and self._is_name(args[state.idx]) is False
                    ):
                        values.append(args[state.idx])
                        state.idx += 1
                    if not values:
                        raise MissingOptionValueError(str(opt.name))
                    for value in values:
                        opt.parse(value)
                    return state
                # not a flag, not n-ary
                if state.idx + 1 >= len(args):
                    raise MissingOptionValueError(str(opt.name))
                opt.parse(args[state.idx + 1])
                state.idx += 2
                return state

        raise RuntimeError("Programmer error: should not reach here!")

    def _parse_named(
        self, name: str, args: list[str], state: _ParsingState
    ) -> _ParsingState:
        """
        Parse a cli argument as a named argument / option.
        Return new index after consuming the argument.
        """
        if name in ["help", "?"]:
            self.print_help()
            raise SystemExit(0)

        for _, child_args in self._children:
            try:
                return child_args._parse_named(name, args, state)
            except UnexpectedOptionError:
                pass

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
                raise UnexpectedOptionError(name)
        opt = self._named_args[self._name2idx[normal_name]]
        if opt.is_parsed and not opt.is_nary:
            raise DuplicateOptionError(str(opt.name))

        if opt.is_flag:
            opt.parse()
            state.idx += 1
            return state
        if opt.is_nary:
            # n-ary option
            values: list[str] = []
            state.idx += 1
            while state.idx < len(args) and self._is_name(args[state.idx]) is False:
                values.append(args[state.idx])
                state.idx += 1
            if not values:
                raise MissingOptionValueError(str(opt.name))
            for value in values:
                opt.parse(value)
            return state

        # not a flag, not n-ary
        if state.idx + 1 >= len(args):
            raise MissingOptionValueError(str(opt.name))
        opt.parse(args[state.idx + 1])
        state.idx += 2
        return state

    def _parse_positional(self, args: list[str], state: _ParsingState) -> _ParsingState:
        """
        Parse a cli argument as a positional argument.
        Return new indices after consuming the argument.
        """

        # skip already parsed positional arguments
        # (because they could have also been named)
        while (
            state.positional_idx < len(self._positional_args)
            and self._positional_args[state.positional_idx].is_parsed
        ):
            state.positional_idx += 1

        if not state.positional_idx < len(self._positional_args):
            if self._var_args:
                self._var_args.parse(args[state.idx])
                state.idx += 1
                return state
            else:
                raise UnexpectedPositionalArgumentError(args[state.idx])

        arg = self._positional_args[state.positional_idx]
        if arg.is_parsed:
            raise DuplicatePositionalArgumentError(args[state.idx])
        if arg.is_nary:
            # n-ary positional arg
            values: list[str] = []
            while state.idx < len(args) and (
                state.positional_only or self._is_name(args[state.idx]) is False
            ):
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

    def _check_completion(self) -> None:
        for child, child_args in self._children:
            try:
                child_args._check_completion()

                # construct the actual object
                init_args, init_kwargs = child_args.make_func_args()
                child._value = child.type_(*init_args, **init_kwargs)  # type: ignore
                child._parsed = True  # type: ignore
            except MissingRequiredOptionError as e:
                # fall back to the child's default only if the user left the
                # whole subtree untouched. if they provided any inner arg,
                # their intent was to build the child, thus surface the error.
                if child.required or child_args._any_parsed_leaf():
                    raise e
                child._value = child.default  # type: ignore
                child._parsed = True  # type: ignore
                continue

        # check that all required args are given first, before assigning any
        # defaults; this keeps `is_parsed` a reliable "user-provided" signal for
        # callers that catch the raise (see `_any_parsed_leaf`).
        for arg in self._positional_args + self._named_args:
            if not arg.is_parsed and arg.required:
                if arg.is_named:
                    # if a positional arg is also named, prefer this type of error message
                    raise MissingRequiredOptionError(str(arg.name))
                else:
                    raise MissingRequiredPositionalArgumentError(str(arg.name))

        # assign defaults to any unparsed optional args
        for arg in self._positional_args + self._named_args:
            if not arg.is_parsed:
                arg._value = arg.default  # type: ignore
                arg._parsed = True  # type: ignore

    def _parse(self, args: list[str]):
        state = _ParsingState()

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
                    except UnexpectedOptionError as e:
                        if self._var_args:
                            self._var_args.parse(args[state.idx])
                            state.idx += 1
                        else:
                            raise e
            else:
                # this must be a positional argument
                state = self._parse_positional(args, state)

        self._check_completion()

    def make_func_args(self) -> tuple[list[Any], dict[str, Any]]:
        """
        Transform parsed arguments into function arguments.

        Returns a tuple of positional arguments and named arguments, such that
        the function can be called like `func(*positional_args, **named_args)`.

        For arguments that are both positional and named, the positional argument
        is preferred, to handle variadic args correctly.
        """

        def var(opt: Arg) -> str:
            return opt.name.long_or_short.replace("-", "_").split(".")[-1]

        positional_args = [arg.value for arg in self._positional_args]
        named_args = {
            var(opt): opt.value
            for opt in self._named_args
            if opt not in self._positional_args and opt.value is not Missing
        }

        if not self._parent and self._var_args and self._var_args.value:
            # Append variadic positional arguments to the end of positional args.
            # This is only done for the top-level Args, not for child Args, as _var_args
            # for child Args is only used to pass remaining args to the parent.
            positional_args += self._var_args.value

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

    def _traverse_args(self) -> tuple[list[Arg], list[Arg], list[Arg]]:
        """
        Recursively traverse all Args and return three lists as a tuple of
        (positional only, positional and named, named only).
        Skips var args and var kwargs.
        """
        positional_only: list[Arg] = []
        positional_and_named: list[Arg] = []
        named_only: list[Arg] = []

        for arg in self._positional_args:
            if arg.args:
                child_pos_only, child_pos_and_named, child_named_only = (
                    arg.args._traverse_args()
                )
                positional_only += child_pos_only
                positional_and_named += child_pos_and_named
                named_only += child_named_only
            else:
                if arg.is_positional and not arg.is_named:
                    positional_only.append(arg)
                elif arg.is_positional and arg.is_named:
                    positional_and_named.append(arg)
        for opt in self._named_args:
            if opt.is_named and not opt.is_positional:
                if opt.args:
                    child_pos_only, child_pos_and_named, child_named_only = (
                        opt.args._traverse_args()
                    )
                    positional_only += child_pos_only
                    positional_and_named += child_pos_and_named
                    named_only += child_named_only
                else:
                    named_only.append(opt)

        return positional_only, positional_and_named, named_only

    def print_help(
        self, console: "Console | None" = None, usage_only: bool = False
    ) -> None:
        """
        Print the help message to the console.

        Args:
            console: A rich console to print to. If None, uses the default console.
            usage_only: Whether to print only the usage line.
        """
        import sys

        from rich.console import Console
        from rich.markdown import Markdown
        from rich.table import Table
        from rich.text import Text

        if self._parent:
            # only the top-level Args can print help
            return self._parent.print_help(console, usage_only)

        name = self.program_name or sys.argv[0]

        positional_only, positional_and_named, named_only = self._traverse_args()

        # (1) print brief if it exists
        console = console or Console()
        console.print()
        if self.brief and not usage_only:
            try:
                md = Markdown(self.brief)
                console.print(md)
                console.print()
            except Exception:
                console.print(self.brief + "\n")

        # (2) then print usage line
        console.print(Text("Usage:", style=Sty.title))
        usage_components: list[Text] = []
        pos_only_str = Text(" ").join([
            usage(arg, "usage line") for arg in positional_only
        ])
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

        console.print(wrap_usage(f"  {name}", usage_components, console.width or 80))

        if usage_only:
            console.print()
            return

        # (3) then print help message for each argument
        console.print(Text("\nwhere", style=Sty.title))

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
                ("-?", f"{Sty.name} {Sty.opt} dim"),
                ("|", f"{Sty.opt} dim"),
                ("--help", f"{Sty.name} {Sty.opt} dim"),
            ),
            "[i dim]Show this help message and exit.[/]",
        )

        console.print(table)
        console.print()
