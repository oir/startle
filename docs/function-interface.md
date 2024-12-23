# CLI from functions

`start()` function translates a given Python function's interface to a 
command-line interface.
It does so by inspecting the given function and defining the command-line arguments and options
based on the function arguments (with their type hints and default values) and the docstring.

More specifically, when you invoke `start(f)`, for a function `f`, it will
- construct an argument parser (based on `f`'s argument type hints, defaults, and docstring),
- parse the command-line arguments, i.e. process raw command-line strings and construct objects
  based on the provided type hints,
- provide the parsed objects as arguments to `f`, and _invoke_ it.

## Example, detailed

Let us revisit the main example to make the above concepts more concrete.

`wc.py`:
```python
from pathlib import Path
from typing import Literal

from startle import start


def word_count(
    fname: Path, /, kind: Literal["word", "char"] = "word", *, verbose: bool = False
) -> None:
    """
    Count the number of words or characters in a file.

    Args:
        fname: The file to count.
        kind: Whether to count words or characters.
        verbose: Whether to print additional info.
    """

    text = open(fname).read()
    count = len(text.split()) if kind == "word" else len(text)

    print(f"{count} {kind}s in {fname}" if verbose else count)


start(word_count)
```

Assume we run our file from the command-line as:
```bash
python wc.py myfile.txt -k char --verbose
```

Then `start(word_count)` will first inspect the `word_count()` function
to construct an argument parser object `Args` which will look like:

```python
Args(brief='Count the number of words or characters in a file.',
     program_name='',
     _positional_args=[Arg(name=Name(short='', long='fname'),
                           type_=<class 'pathlib.Path'>,
                           is_positional=True,
                           is_named=False,
                           is_nary=False,
                           help='The file to count.',
                           metavar='path',
                           default=None,
                           required=True),
                       Arg(name=Name(short='k', long='kind'),
                           type_=typing.Literal['word', 'char'],
                           is_positional=True,
                           is_named=True,
                           is_nary=False,
                           help='Whether to count words or characters.',
                           metavar=['word', 'char'],
                           default='word',
                           required=False)],
     _named_args=[Arg(name=Name(short='k', long='kind'),
                      type_=typing.Literal['word', 'char'],
                      is_positional=True,
                      is_named=True,
                      is_nary=False,
                      help='Whether to count words or characters.',
                      metavar=['word', 'char'],
                      default='word',
                      required=False),
                  Arg(name=Name(short='v', long='verbose'),
                      type_=<class 'bool'>,
                      is_positional=False,
                      is_named=True,
                      is_nary=False,
                      help='Whether to print additional info.',
                      metavar=['true', 'false'],
                      default=False,
                      required=False)])
```
_(some fields are omitted for illustration)_

Our (simplified) function signature looks like:
```
def word_count(fname, /, kind, *, verbose):
               -----     ----     -------
               |          |             |
               |      Positional        |
               |      or keyword        - Keyword only
               |
               -- Positional only
```
using the delimiters `/` and `*`.

As a result, we see that the resulting `Args` object contains two
positional arguments (one for `fname`, and one for `kind`), and
two named arguments / options (one for `kind`, and one for `verbose`).
Note that `kind`, given that it is declared "positional _or_ keyword",
appears in both lists as expected, whereas `fname` becomes a positional-only
argument and `verbose` becomes named-only argument (or option).

Further observe how the `Arg` objects have their assigned `type_`s
based on the hints in `word_count()`, as well as their default values
(which determines if an argument is required or optional), and
their `help` strings.

Once the `Args` parser is constructed, `Args.parse()` will be invoked using
the command line arguments we specified: `["myfile.txt", "-k", "char", "--verbose"]`

This will result in the following _parsed_ objects for each argument:
- ```python
  Arg(name=Name(short='', long='fname'), ..., _value=PosixPath('myfile.txt'))
  ```
- ```python
  Arg(name=Name(short='k', long='kind'), ..., _value='char')
  ```
- ```python
  Arg(name=Name(short='v', long='verbose'), ..., _value=True)
  ```
Observer how internal `_value` fields contain the concrete parsed values.

Finally, these values are translated into appropriate positional and keyword
arguments as `word_count` expects them, and the function is called:
```python
f_args = [PosixPath('myfile.txt'), 'char']
f_kwargs = {"verbose": True}
word_count(*f_args, **f_kwargs)
```

This gives us the final output:
```bash
~ ❯ python examples/wc.py myfile.txt -k char --verbose
590 chars in examples/wc.py
~ ❯
```

## Argument specification

This subsection provides more detail about how a function argument is translated
into a command-line argument for the parser.

- **Name:** Option names are obtained from the name of the argument in the function
  definition, as is, except any `"_"` is replaced by `"-"`.
  
  If the function argument 
  name is long (more than 1 character), it is used as the "long" name of the option,
  to be used with `--` prefix. In this case, first letter of the argument name is 
  used to define the "short" name, if it's available.
  If the function argument name is short (1 character), it is used as the "short"
  name and the CLI argument will not have a long name.

  Argument name is less important for positional arguments since it is not used
  when passing it in, however it is still used as part of the help string.
  Automatic short name is not generated for positional arguments since it is not
  needed.

  Some examples:
  - ```python
    def magic_missile(direction: str, mana_cost: float):
    ```
    - `-d, --direction`
    - `-m, --mana-cost`
  - ```python
    def magic_missile(missile_direction: str, mana_cost: float):
    ```
    - `-m, --missile-direction`
    - `--mana-cost`
  - ```python
    def magic_missile(missile_direction: str, /, mana_cost: float):
    ```
    - `missile-direction`
    - `-m, --mana-cost`

- **Type:** Target type after parsing the argument is directly obtained from the type
  hint assigned to the function argument.
  See [Types and parsing rules](types#types-and-parsing-rules) for
  detailed information how each such type is parsed.

- **Positional arg vs option:** Python functions can (optionally) use `/` and `*` delimiters to
  designate a function argument as a "positional only", "keyword only", or both.

  ```python
  def word_count(fname, /, kind, *, verbose):
      """        -----     ----     -------
                 |          |             |
                 |      Positional        |
                 |      or keyword        - Keyword only
                 |
                 -- Positional only                     """
  ```
  This directly translates into the same notion for command-line arguments.
  Positonal only function arguments become positional command-line arguments,
  and keyword only function arguments become command-line options.
  Function arguments that are both become command-line arguments that could be
  fed in either as a positional argument or an option, during command-line
  invocation.

