# Functions

## `start()`

```python
def start(
    obj: Callable | list[Callable] | dict[str, Callable],
    *,
    args: list[str] | None = None,
    catch: bool = True,
) -> Any
```

Given a function, or a container of functions `obj`, parse its arguments from the command-line and call it.

### Parameters: <!-- {docsify-ignore} -->

| Name | Type | Description | Default |
|------|------|-------------|---------|
| `obj` | <span class="codey"> Callable \| list[Callable] \| dict[str, Callable] </span> | The function or functions to parse the arguments for and invoke. If a list or dict, the functions are treated as subcommands. | _required_ |
| `args` | <span class="codey"> list[str] \| None </span> | The arguments to parse. If None, uses the arguments from the command-line (i.e. sys.argv). | `None` |
| `catch` | <span class="codey"> bool </span> | Whether to catch and print (startle specific) errors instead of raising. This is used to display a more presentable output when a parse error occurs instead of the default traceback. This option will never catch non-startle errors. | `True` |


### Returns: <!-- {docsify-ignore} -->

| Type | Description |
|------|-------------|
| `Any` | The return value of the function `obj`, or the subcommand of `obj` if it is a list or dict. |



## `parse()`

```python
def parse(
    cls: type[~T],
    *,
    args: list[str] | None = None,
    brief: str = '',
    catch: bool = True,
) -> ~T
```

Given a class `cls`, parse arguments from the command-line according to the class definition and construct an instance.

### Parameters: <!-- {docsify-ignore} -->

| Name | Type | Description | Default |
|------|------|-------------|---------|
| `cls` | <span class="codey"> type[~T] </span> | The class to parse the arguments for and construct an instance of. | _required_ |
| `args` | <span class="codey"> list[str] \| None </span> | The arguments to parse. If None, uses the arguments from the command-line (i.e. sys.argv). | `None` |
| `brief` | <span class="codey"> str </span> | The brief description of the parser. This is used to display a brief when --help is invoked. | `''` |
| `catch` | <span class="codey"> bool </span> | Whether to catch and print (startle specific) errors instead of raising. This is used to display a more presentable output when a parse error occurs instead of the default traceback. This option will never catch non-startle errors. | `True` |


### Returns: <!-- {docsify-ignore} -->

| Type | Description |
|------|-------------|
| `~T` | An instance of the class `cls`. |



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


