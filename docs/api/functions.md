# Functions

## `start()`

```python
def start(
    obj: Callable | list[Callable] | dict[str, Callable],
    args: list[str] | None = None,
    caught: bool = True,
) -> Any
```

Given a function, or a container of functions `obj`, parse its arguments from the command-line and call it.

### Parameters: <!-- {docsify-ignore} -->

| Name | Type | Description | Default |
|------|------|-------------|---------|
| `obj` | <span class="codey"> Callable \| list[Callable] \| dict[str, Callable] </span> | The function or functions to parse the arguments for and invoke. If a list or dict, the functions are treated as subcommands. | _required_ |
| `args` | <span class="codey"> list[str] \| None </span> | The arguments to parse. If None, uses the arguments from the command-line (i.e. sys.argv). | `None` |
| `caught` | <span class="codey"> bool </span> | Whether to catch and print errors instead of raising. This is used to display a more presentable output when a parse error occurs instead of the default traceback. | `True` |


### Returns: <!-- {docsify-ignore} -->

| Type | Description |
|------|-------------|
| `Any` | The return value of the function `obj`, or the subcommand of `obj` if it is a list or dict. |
## `register()`

```python
def register(
    type_: type,
    parser: Callable[[str], Any] | None = None,
    metavar: str | list[str] | None = None,
) -> None
```

Register a custom parser and metavar for a type. `parser` can be omitted to specify a custom metavar for an already parsable type.

### Parameters: <!-- {docsify-ignore} -->

| Name | Type | Description | Default |
|------|------|-------------|---------|
| `type_` | <span class="codey"> type </span> | The type to register the parser and metavar for. | _required_ |
| `parser` | <span class="codey"> Callable[[str], Any] \| None </span> | A function that takes a string and returns a value of the type. | `None` |
| `metavar` | <span class="codey"> str \| list[str] \| None </span> | The metavar to use for the type in the help message. If None, default metavar "val" is used. If list, the metavar is treated as a literal list of possible choices, such as ["true", "false"] yielding "true\|false" for a boolean type. | `None` |


