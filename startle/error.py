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


class MissingOptionNameError(ParserOptionError):
    """
    Exception raised when `-` does not have a name following it.
    """

    def __init__(self) -> None:
        super().__init__("Prefix `-` is not followed by an option!")


class UnexpectedOptionError(ParserOptionError):
    """
    Exception raised when an unexpected option is provided to the parser.
    """

    def __init__(self, name: str) -> None:
        super().__init__(f"Unexpected option `{name}`!")


class DuplicateOptionError(ParserOptionError):
    """
    Exception raised when a duplicate option is provided to the parser when it is not n-ary.
    """

    def __init__(self, name: str) -> None:
        super().__init__(f"Option `{name}` is multiply given!")


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
