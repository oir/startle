from typing import Any


class ParserOptionError(Exception):
    """
    Exception raised when there is an error providing an option to the parser.
    """

    pass


class ParserValueError(ValueError):
    """
    Exception raised when there is an error parsing a value.
    """

    pass


class ParserConfigError(Exception):
    """
    Exception raised when there is an error in the parser configuration
    (during construction of the parser, prior to parsing).
    """

    pass


# Below are the specific errors derived from one of the above base errors


class ValueParsingError(ParserValueError):
    """
    Exception raised when a value cannot be parsed to the expected type.
    """

    def __init__(self, value: str, type_: str) -> None:
        super().__init__(f"Cannot parse {type_} from `{value}`!")


class UnsupportedValueTypeError(ParserValueError):
    """
    Exception raised when a value type is unsupported for parsing.
    """

    def __init__(self, type_: Any) -> None:
        super().__init__(f"Unsupported type `{type_}`!")


class MissingOptionNameError(ParserOptionError):
    """
    Exception raised when `-` does not have a name following it.
    """

    def __init__(self) -> None:
        super().__init__("Prefix `-` is not followed by an option!")


class MissingOptionValueError(ParserOptionError):
    """
    Exception raised when an option is missing an argument value
    (e.g. `--option` is given but no value follows).
    """

    def __init__(self, name: str) -> None:
        super().__init__(f"Option `{name}` is missing argument!")


class MissingRequiredOptionError(ParserOptionError):
    """
    Exception raised when a required option is missing.
    """

    def __init__(self, name: str) -> None:
        super().__init__(f"Required option `{name}` is not provided!")


class MissingRequiredPositionalArgumentError(ParserOptionError):
    """
    Exception raised when a required positional argument is missing.
    """

    def __init__(self, long_name: str) -> None:
        super().__init__(f"Required positional argument <{long_name}> is not provided!")


class UnexpectedOptionError(ParserOptionError):
    """
    Exception raised when an unexpected option is provided to the parser.
    """

    def __init__(self, name: str) -> None:
        super().__init__(f"Unexpected option `{name}`!")


class UnexpectedPositionalArgumentError(ParserOptionError):
    """
    Exception raised when an unexpected positional argument is provided to the parser.
    """

    def __init__(self, value: str) -> None:
        super().__init__(f"Unexpected positional argument: `{value}`!")


class DuplicateOptionError(ParserOptionError):
    """
    Exception raised when a duplicate option is provided to the parser when it is not n-ary.
    """

    def __init__(self, name: str) -> None:
        super().__init__(f"Option `{name}` is multiply given!")


class DuplicatePositionalArgumentError(ParserOptionError):
    """
    Exception raised when a duplicate positional argument is provided to the parser when it is not n-ary.
    This is practically impossible to happen via command-line input, but kept for
    completeness and programming errors.
    """

    def __init__(self, name: str) -> None:
        super().__init__(f"Positional argument `{name}` is multiply given!")


class FlagWithValueError(ParserOptionError):
    """
    Exception raised when a flag option is provided with a value via --option=value syntax.
    """

    def __init__(self, name: str) -> None:
        super().__init__(f"Option `{name}` is a flag and cannot be assigned a value!")


class NonFlagInShortNameCombinationError(ParserOptionError):
    """
    Exception raised when a non-flag option is used in a short name combination (e.g. -abc),
    not as the last one.
    """

    def __init__(self, name: str) -> None:
        super().__init__(f"Option `{name}` is not a flag and cannot be combined!")


class MissingCommandError(ParserOptionError):
    """
    Exception raised when no command is given and there is no default command.
    """

    def __init__(self) -> None:
        super().__init__("No command given!")


class UnexpectedCommandError(ParserOptionError):
    """
    Exception raised when an unknown command is given and there is no default command.
    """

    def __init__(self, cmd: str) -> None:
        super().__init__(f"Unknown command `{cmd}`!")


class NameCollisionError(ParserConfigError):
    """
    Exception raised when there is a name collision in the parser configuration during
    recursive parsing with `flat` naming.
    """

    def __init__(self, name: str, obj_name: str) -> None:
        super().__init__(
            f"Option name `{name}` is used multiple times in `{obj_name}`!"
            " Recursive parsing with `flat` naming requires unique option names among all levels."
        )


class HelpCollisionError(ParserConfigError):
    """
    Exception raised when `help` is used as a parameter name.
    """

    def __init__(self, obj_name: str) -> None:
        super().__init__(f"Cannot use `help` as parameter name in `{obj_name}`!")


class VariadicChildParamError(ParserConfigError):
    """
    Exception raised when a variadic parameter is found in child Args during recursive parsing.
    """

    def __init__(self, param_name: str, obj_name: str) -> None:
        super().__init__(
            f"Cannot have variadic parameter `{param_name}` in child Args of `{obj_name}`!"
        )


class VariadicNonRecursableParamError(ParserConfigError):
    def __init__(self, param_name: str, obj_name: str) -> None:
        super().__init__(
            f"Cannot recurse into variadic parameter `{param_name}` in `{obj_name}`!"
        )


class NaryNonRecursableParamError(ParserConfigError):
    def __init__(self, param_name: str, obj_name: str) -> None:
        super().__init__(
            f"Cannot recurse into n-ary parameter `{param_name}` in `{obj_name}`!"
        )


class NonClassNonRecursableParamError(ParserConfigError):
    def __init__(self, param_name: str, annotation: Any, obj_name: str) -> None:
        super().__init__(
            f"Cannot recurse into parameter `{param_name}` of non-class type "
            f"`{annotation}` in `{obj_name}`!"
        )


class UnsupportedTypeError(ParserConfigError):
    """
    Exception raised when an unsupported type is encountered during parser construction.
    """

    def __init__(self, param_name: str, annotation: Any, obj_name: str) -> None:
        super().__init__(
            f"Unsupported type `{annotation}` for parameter `{param_name}` in `{obj_name}`!"
        )


class MissingNameError(ParserConfigError):
    """
    Exception raised when both long and short names are missing when initializing `Name`.
    """

    def __init__(self) -> None:
        super().__init__("Named arguments should have at least one name!")


class MissingContainerTypeError(ParserConfigError):
    """
    Exception raised when a n-ary parameter is missing a container type.
    """

    def __init__(self) -> None:
        super().__init__("Container type must be specified for n-ary options!")


class ArgumentKindError(ParserConfigError):
    """
    Exception raised when an argument is neither positional nor named.
    """

    def __init__(self) -> None:
        super().__init__("An argument should be either positional or named (or both)!")


class UnsupportedContainerTypeError(ParserConfigError):
    """
    Exception raised when an unsupported container type is used for n-ary options.
    """

    def __init__(self) -> None:
        super().__init__("Unsupported container type!")


class UnexpectedDefaultCommandError(ParserConfigError):
    """
    Exception raised when the default command is not among the subcommands.
    """

    def __init__(self, default: str, available_cmds: list[str]) -> None:
        super().__init__(
            f"Default command `{default}` is not among the subcommands!"
            f" Available subcommands: {', '.join(available_cmds)}"
        )


class CmdsRecurseError(ParserConfigError):
    """
    Exception raised when recurse==True for Cmds, which is not yet supported.
    """

    def __init__(self) -> None:
        super().__init__("Recurse option is not yet supported for multiple functions.")


class SingleFunctionDefaultCommandError(ParserConfigError):
    """
    Exception raised when a default command is given for a single function.
    """

    def __init__(self) -> None:
        super().__init__("Default subcommand is not supported for a single function!")
