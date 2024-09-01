from typing import Literal, Any
from dataclasses import dataclass


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

    def convert(self, type_: type) -> Any:
        # check if a method named `to_<type_.__name__>` exists
        method_name = f"to_{type_.__name__}"
        if hasattr(self, method_name):
            return getattr(self, method_name)()
        raise ParserValueError(f"Cannot parse argument to type {type_.__name__}!")


@dataclass
class Arg:
    type_: type
    help: str = ""
    metavar: str = ""
    default: Any = None
    required: bool = False

    # Note: an Arg can be both positional and named.
    names: list[str] | None = None
    positional: bool = False

    _parsed: bool = False  # if this is already parsed
    _nargs: bool = False  # if this is n-ary

    _value: Any = None  # the parsed value

    def parse(self, value: str):
        self._value = ValueParser(value).convert(self.type_)
        self._parsed = True


def ensure(condition: bool, message: str, error_cls=ValueError):
    if not condition:
        raise error_cls(message)


class Args:
    _positional_args: list[Arg]
    _named_args: list[Arg]
    _name2idx: dict[str, int]

    def __init__(self):
        self._positional_args = []
        self._named_args = []
        self._name2idx = {}

    @staticmethod
    def is_name(value: str) -> str | Literal[False]:
        if value.startswith("--"):
            name = value[2:]
            ensure(name, "Prefix `--` not followed by an option!")
            return name
        if value.startswith("-"):
            name = value[1:]
            ensure(name, "Prefix `-` not followed by an option!")
            ensure(
                len(name) == 1,
                "Options prefixed by `-` have to be short names! "
                "Did you mean `--" + name + "`?",
            )
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
            positional=positional,
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
                if name not in self._name2idx:
                    raise ParserOptionError(f"Unexpected option `{name}`!")
                opt = self._named_args[self._name2idx[name]]
                ensure(
                    not opt._parsed,
                    f"Option `{name}` is multiply given!",
                    ParserOptionError,
                )

                # TODO: flags and n-aries

                # assuming nonflag & n-ary now
                ensure(
                    idx + 1 < len(args),
                    f"Option `{name}` is missing argument!",
                    ParserOptionError,
                )
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
            import sys

            self._parse(sys.argv[1:])
        return self

    def __repr__(self) -> str:
        rval = "<Args object>\n"
        for arg in self._positional_args:
            rval += f"  <positional> {arg.metavar}: {arg._value}\n"
        for arg in self._named_args:
            rval += f"  <named> {','.join(arg.names)}: {arg._value}\n"
        return rval
