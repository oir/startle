# Types and Parsing Rules

This section describes how the parsing is performed for a type specified in your hints.
That is, how a raw string argument is processed to construct an object with the designated type.

## Supported (Built-in) Types

| Type (hint) | Parsed value for argument string `s` | Metavar |
| ---- | ------------- | ------- |
| `str` | `s` | `<text>` |
| `int` | `int(s)` | `<int>` |
| `float` | `float(s)` | `<float>` |
| `bool` | `True` if lowercased `s` is in `["true", "t", "yes", "y", "1"]` <br> `False` if lowercased `s` is in `["false", "f", "no", "n", "0"]` <br> parse error otherwise | `true\|false` |
| `pathlib.Path` | `pathlib.Path(s)` | `<path>` |
| `T(enum.StrEnum)` or <br> `T(str, enum.Enum)` | `T.OPT_I` for an enum option with `s == T.OPT_I.value` <br> parse error otherwise | `T.OPT_1.value\|...\|T.OPT_N.value` |
| Other enum types, `T(enum.Enum)` | `T.OPT_I` for an enum option with `s == "opt-i"` <br> parse error otherwise | `opt-1\|...\|opt-n` |
| `typing.Literal["opt-1", ..., "opt-n"]` | `s` if `s` is in `["opt-1", ..., "opt-n"]` <br> parse error otherwise | `opt-1\|...\|opt-n` |
| `T \| None` or <br> `typing.Optional[T]` or <br> `typing.Union[T, None]` | parse as if `T` | metavar as if `T` |

_Note: Metavar column shows how the input value is represented in the help string._

- **Enums:** Observe that string based enums (classes inheriting from `enum.StrEnum`, or
  multiply inheriting from both `str` and `enum.Enum`)
  are expected to be specified by their _values_, whereas any other enum type is expected
  to be specified by their _keys_ (or variable names).
  
  In the latter case, expected string representation is `name.lower().replace("_", "-")`, e.g.
  for an enum option `MyEnum.SOME_CHOICE`, one needs to feed in `some-choice` from the command line.

- **Optional types:** Observe that optional types are treated as if they are the inner type `T`.
  This means that it is not possible to specify a `None` value from the command line
  (unless parsing for `T` somehow results in a `None` value). 
  Therefore, the intended use case
  for optional types is to have a default value as `None`, such that not feeding the argument / option
  would let the variable attain a `None` value.
  
  For example:
  ```python
  def hello(name: str | None = None):
      pass
  ```


### n-ary Arguments

The following type hints turn an argument (or an option) to _n-ary_, meaning that for a container
of type `T`, multiple string arguments from the command line are repeatedly parsed as `T`s and
appended to the container.


| Type (hint) | Parsed value given `args: list[str]` as a list of command line arguments |
| ---- | ------------- | 
| `list[T]` or `typing.List[T]` | `[parse_T(arg) for arg in args]` <br> where `parse_T()` denotes the parsing method for `T` |
| `list` | `args` (thus, `list` is treated as the same as `list[str]`) |
| `tuple[T]` or `typing.Tuple[T]` | `tuple([parse_T(arg) for arg in args])` <br> where `parse_T()` denotes the parsing method for `T` |
| `tuple` | `tuple(args)` |
| `set[T]` or `typing.Set[T]` | `set([parse_T(arg) for arg in args])` <br> where `parse_T()` denotes the parsing method for `T` |
| `set` | `set(args)` |

## User Defined Types

Any custom type that is not supported out of the box can be supported by registering it with `register_type()`.
To register such a type `T`, you need to define
- a parser, which is a function (callable) that takes in a `str` and returns a `T`
  (and can raise a `startle.error.ParserValueError` if needed)
- and optionally a metavar as either
  - a string (for most types, to be enclosed by `<>`),
  - or a list of strings (for choice-based types, to be joined by `|`)
  to 
