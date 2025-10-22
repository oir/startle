from collections.abc import Iterable
from inspect import Parameter, signature


def get_class_initializer_params(cls: type) -> Iterable[tuple[str, Parameter]]:
    """
    Get the parameters of the class's `__init__` method, excluding `self`.
    """
    func = cls.__init__  # type: ignore
    # (mypy thinks cls is an instance)

    # Get the signature of the initializer
    sig = signature(func)

    # name of the first parameter (usually `self`)
    self_name = next(iter(sig.parameters))

    # filter out the first parameter
    return [
        (name, param) for name, param in sig.parameters.items() if name != self_name
    ]
