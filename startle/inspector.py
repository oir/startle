from typing import get_type_hints, Optional, Union, get_origin, get_args
import inspect
from inspect import getmembers
from .parser import Args
import types


def make_args(func: callable) -> Args:
    args = Args()

    # Get the signature of the function
    sig = inspect.signature(func)

    # Helper function to normalize type annotations
    def normalize_type(annotation):
        origin = get_origin(annotation)
        args = get_args(annotation)
        pod_types = {int, float, str, bool}
        if (
            (origin is Union or origin is types.UnionType)
            and len(args) == 2
            and type(None) in args
        ):
            return Optional[args[0] if args[1] is type(None) else args[1]]
        elif origin is None and annotation is not None:
            # Handle bar syntax (POD | None)
            for pod_type in pod_types:
                if annotation == Union[pod_type, None]:
                    return Optional[pod_type]
        return annotation

    # Iterate over the parameters and determine their kind
    for param_name, param in sig.parameters.items():
        normalized_annotation = normalize_type(param.annotation)

        if param.default is not inspect.Parameter.empty:
            required = False
            default = param.default
        else:
            required = True
            default = None

        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            args.add(
                normalized_annotation,
                positional=True,
                metavar=param_name,
                required=required,
                default=default,
            )
        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.add(
                normalized_annotation,
                names=[param_name],
                required=required,
                default=default,
            )
        elif param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            args.add(
                normalized_annotation,
                positional=True,
                metavar=param_name,
                names=[param_name],
                required=required,
                default=default,
            )

    return args
