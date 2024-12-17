# Types and Parsing Rules

This section describes how the parsing is performed for a type specified in your hints.
That is, how a raw string argument is processed to construct an object with the designated type.

## Supported (Built-in) Types

| Type | Parsed value for argument string `s` | Metavar |
| ---- | ------------- | ------- |
| `str` | `s` | `<text>` |
| `int` | `int(s)` | `<int>` |
| `float` | `float(s)` | `<float>` |
| `bool` | `True` if lowercased `s` is one of `["true", "t", "yes", "y", "1"]` <br> `False` if lowercased `s` is one of `["false", "f", "no", "n", "0"]` <br> parse error otherwise | `true\|false` |
| `pathlib.Path` | `pathlib.Path(s)` | `<path>` |
| `T(enum.StrEnum)` or <br> `T(str, enum.Enum)` | `T.OPT` for an enum option with `s == T.OPT.value` <br> parse error otherwise | `T.OPT1.value\|...\|T.OPTN.value` |

## User Defined Types