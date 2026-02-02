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
    Exception raised when a parameter is missing a name.
    """

    def __init__(self) -> None:
        super().__init__("Named arguments should have at least one name!")


class MissingContainerTypeError(ParserConfigError):
    """
    Exception raised when a n-ary parameter is missing a container type.
    """

    def __init__(self) -> None:
        super().__init__("Container type must be specified for n-ary options!")
