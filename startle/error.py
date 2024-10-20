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
