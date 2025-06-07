import inspect
import types
from collections import abc
from typing import Any, Callable, TextIO, Union, get_args, get_origin

from startle import parse, register, start
from startle.inspect import _parse_func_docstring


def _shorten_type_annotation(annotation: Any) -> str:
    origin = get_origin(annotation)
    if origin is None:
        # It's a simple type, return its name
        if inspect.isclass(annotation):
            return annotation.__name__
        return str(annotation)

    # Handle Optional types explicitly
    if origin is Union or origin is types.UnionType:
        args = get_args(annotation)
        if type(None) in args:
            args = tuple([arg for arg in args if arg is not type(None)])
            return " | ".join(_shorten_type_annotation(arg) for arg in args) + " | None"
        return " | ".join(_shorten_type_annotation(arg) for arg in args)

    if origin is Callable or origin is abc.Callable:
        args = get_args(annotation)
        if args:
            args_str = ", ".join(_shorten_type_annotation(arg) for arg in args[0])
            return f"Callable[[{args_str}], {_shorten_type_annotation(args[1])}]"
        return "Callable"

    # It's a generic type, process its arguments
    args = get_args(annotation)
    if args:
        args_str = ", ".join(_shorten_type_annotation(arg) for arg in args)
        return f"{origin.__name__}[{args_str}]"

    return str(annotation).removeprefix("typing.")


def _parse_return_description(func: Callable) -> str:
    """
    Parse the return description of a function from its docstring.
    """
    docstring = inspect.getdoc(func)
    if not docstring:
        return ""

    lines = docstring.split("\n")
    i = 0
    while i < len(lines) and lines[i].strip() != "Returns:":
        i += 1
    i += 1

    return_description = ""
    while i < len(lines) and lines[i].strip() != "" and lines[i].startswith(" "):
        if return_description:
            return_description += " "
        return_description += lines[i].strip()
        i += 1

    return return_description


def func_api(func: Callable, file: TextIO):
    """
    Given a function `func`, print its docstrings and signature with
    type hints.
    """
    print(f"## `{func.__name__}()`\n", file=file)

    sig = inspect.signature(func)
    print("```python", file=file)
    print(f"def {func.__name__}(", file=file)
    last_param_kind = None
    for param in sig.parameters.values():
        maybe_default = ""
        if param.default is not inspect.Parameter.empty:
            maybe_default = f" = {repr(param.default)}"
        if (
            last_param_kind is not inspect.Parameter.KEYWORD_ONLY
            and param.kind is inspect.Parameter.KEYWORD_ONLY
        ):
            print("    *,", file=file)
        print(
            f"    {param.name}: {_shorten_type_annotation(param.annotation)}{maybe_default},",
            file=file,
        )
        last_param_kind = param.kind
    print(f") -> {_shorten_type_annotation(sig.return_annotation)}", file=file)
    print("```\n", file=file)

    brief, arg_helps = _parse_func_docstring(func)

    print(f"{brief}\n", file=file)

    print("### Parameters: <!-- {docsify-ignore} -->\n", file=file)

    print("| Name | Type | Description | Default |", file=file)
    print("|------|------|-------------|---------|", file=file)
    for param in sig.parameters.values():
        name = f"`{param.name}`"
        typ = _shorten_type_annotation(param.annotation).replace("|", "\\|")
        typ = f'<span class="codey"> {typ} </span>'
        desc = arg_helps.get(param.name, "").replace("|", "\\|")
        default = param.default
        if default is inspect.Parameter.empty:
            default = "_required_"
        else:
            default = f"`{repr(default)}`"
        print(f"| {name} | {typ} | {desc} | {default} |", file=file)

    print("\n", file=file)

    if sig.return_annotation is None:
        return

    print("### Returns: <!-- {docsify-ignore} -->\n", file=file)

    print("| Type | Description |", file=file)
    print("|------|-------------|", file=file)
    rt = _shorten_type_annotation(sig.return_annotation).replace("|", "\\|")
    rt = f"`{rt}`"
    desc = _parse_return_description(func)
    print(f"| {rt} | {desc} |", file=file)
    print("\n\n", file=file)


if __name__ == "__main__":
    with open("docs/api/functions.md", "w") as f:
        print("# Functions\n", file=f)
        func_api(start, f)
        func_api(parse, f)
        func_api(register, f)
